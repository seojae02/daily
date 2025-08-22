from fastapi import APIRouter, File, Form, UploadFile, Query, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List, Optional
import io, json
import torch
from PIL import ImageDraw, ImageOps
from diffusers import StableDiffusionInpaintPipeline
from rembg import remove
import google.generativeai as genai
from config import GEMINI_API_KEY, MODEL_ID
from utils import read_image_from_upload, resize_image, parse_ratio_and_size, get_position_coords, draw_text_with_background

router = APIRouter()

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32
INPAINT_PIPE = None

genai.configure(api_key=GEMINI_API_KEY)

@router.post("/v1/ad-image")
def ad_image(
    input_image: UploadFile = File(..., description="기준 이미지(PNG/JPG)"),
    user_prompt: str = Form(..., description="배경 컨셉 설명(자연어, 한국어 OK)"),
    resize_mode: str = Form("pad", description="pad|crop"),
    ratio: Optional[str] = Form("1:1", description="예: 1:1, 4:5, 16:9"),
    base_size: Optional[int] = Form(512, description="짧은 변 기준 크기"),
    elements_json: Optional[str] = Form(None, description="텍스트/로고 요소 배열 JSON"),
    logos: Optional[List[UploadFile]] = File(None, description="로고 이미지들(선택)"),
    return_mode: str = Query("image", alias="return", description="image|json"),
):
    global INPAINT_PIPE
    if INPAINT_PIPE is None:
        try:
            INPAINT_PIPE = StableDiffusionInpaintPipeline.from_pretrained(
                "runwayml/stable-diffusion-inpainting", torch_dtype=DTYPE, safety_checker=None
            ).to(DEVICE)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Inpaint 파이프라인 로딩 실패: {e}")

    try:
        ref_image = read_image_from_upload(input_image)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"입력 이미지 오류: {e}")

    target_w, target_h = parse_ratio_and_size(ratio, base_size)
    ref_resized = resize_image(ref_image, target_w, target_h, resize_mode)

    try:
        foreground_mask = remove(ref_resized, only_mask=True)
        background_mask = ImageOps.invert(foreground_mask)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"마스크 생성 실패: {e}")

    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        final_prompt = (
            "You are an expert prompt engineer for Stable Diffusion Inpainting.\n"
            "Return ONLY a single concise English prompt that vividly describes a NEW BACKGROUND matching the user's concept.\n"
            "Do NOT mention text, logos, watermarks, or people. Focus on atmosphere, lighting, environment, and style.\n"
            f"User concept (Korean allowed): {user_prompt}\n"
        )
        buf = io.BytesIO()
        ref_resized.save(buf, format="PNG")
        buf.seek(0)
        gem_resp = model.generate_content([
            final_prompt,
            {"mime_type": "image/png", "data": buf.getvalue()},
        ])
        generated_prompt = (gem_resp.text or "").strip()
        if not generated_prompt:
            raise ValueError("빈 프롬프트")
    except Exception as e:
        generated_prompt = (
            "cinematic wide background, moody atmosphere, soft volumetric lighting, "+
            "depth of field, photorealistic, rich textures, high detail"
        )
        print(f"[경고] Gemini 보조 프롬프트 실패 → 기본 프롬프트 사용: {e}")

    try:
        with torch.no_grad():
            result = INPAINT_PIPE(
                prompt=generated_prompt,
                image=ref_resized,
                mask_image=background_mask,
                width=target_w,
                height=target_h,
                guidance_scale=7.5,
                num_inference_steps=50,
                negative_prompt=(
                    "text, logo, watermark, blurry, low quality, distorted, bad quality, "
                    "clutter, extra objects, repeated patterns, overexposed, artifacts"
                ),
            )
        gen_img = result.images[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inpainting 실패: {e}")

    draw = ImageDraw.Draw(gen_img)
    W, H = gen_img.size
    loaded_logos: List[Image.Image] = []
    if logos:
        for lf in logos:
            try:
                loaded_logos.append(Image.open(io.BytesIO(lf.file.read())).convert("RGBA"))
            except Exception:
                loaded_logos.append(None)

    elements: List[dict] = []
    if elements_json:
        try:
            elements = json.loads(elements_json)
            if not isinstance(elements, list):
                raise ValueError("elements_json은 배열이어야 합니다.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"elements_json 파싱 오류: {e}")

    def load_font(path: str, size: int):
        if path:
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
        return ImageFont.load_default()

    for el in elements:
        try:
            etype = el.get("type")
            if etype in ("text", "bg_text"):
                font = load_font(el.get("font") or "", int(el.get("size", 48)))
                if etype == "text":
                    x, y = get_position_coords(el.get("position", "center-center"), W, H)
                    draw.text((x, y), el.get("text", ""), font=font, fill=el.get("color", "white"), anchor="mm")
                else:
                    draw_text_with_background(draw, el, font, W, H)
            elif etype == "logo":
                idx = int(el.get("logo_index", 0))
                scale = float(el.get("scale", 0.2))
                if 0 <= idx < len(loaded_logos) and loaded_logos[idx] is not None:
                    logo_img = loaded_logos[idx]
                    logo_w = max(1, int(W * max(0.05, min(0.8, scale))))
                    logo_h = max(1, int(logo_w / logo_img.width * logo_img.height))
                    logo_resized = logo_img.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
                    x, y = get_position_coords(el.get("position", "bottom-right"), W, H)
                    lx, ly = int(x - logo_w / 2), int(y - logo_h / 2)
                    gen_img.paste(logo_resized, (lx, ly), logo_resized)
        except Exception as e:
            print(f"[요소 경고] 요소 적용 실패: {e}")

    if return_mode == "json":
        out_buf = io.BytesIO()
        gen_img.save(out_buf, format="JPEG", quality=95)
        b64 = base64.b64encode(out_buf.getvalue()).decode("utf-8")
        return JSONResponse({
            "width": W,
            "height": H,
            "prompt": generated_prompt,
            "image_base64": b64,
        })
    else:
        out_buf = io.BytesIO()
        gen_img.save(out_buf, format="JPEG", quality=95)
        out_buf.seek(0)
        headers = {"Content-Disposition": "inline; filename=ad_image.jpg"}
        return StreamingResponse(out_buf, media_type="image/jpeg", headers=headers)
