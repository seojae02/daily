"""
FastAPI backend that combines:
1) Promo text generation via Gemini **REST** (multipart form: images + text) — `/v1/generate-promo`
2) Ad-image generation pipeline (rembg + Stable Diffusion Inpaint + Gemini SDK prompt assist) — `/v1/ad-image`

Run:
  uvicorn fastapi_merged_app:app --host 0.0.0.0 --port 8000 --log-level info

.env (same dir):
  GEMINI_API_KEY=YOUR_KEY
  GEMINI_MODEL=gemini-1.5-flash   # optional, defaults to gemini-1.5-flash

requirements.txt (suggested):
  fastapi
  uvicorn[standard]
  python-dotenv
  requests
  pillow
  google-generativeai
  torch  # pick a version compatible with your CUDA/CPU
  diffusers
  rembg

Curl (promo text):
  curl -X POST 'http://localhost:8000/v1/generate-promo' \
    -F 'store_name=피자킹' \
    -F 'mood=활기찬' \
    -F 'store_description=석쇠 화덕 피자 전문점' \
    -F 'location_text=서울 성동구' \
    -F 'variants=3' \
    -F 'language=ko' \
    -F 'store_images=@./sample_store.jpg;type=image/jpeg' \
    -F 'food_images=@./sample_food.jpg;type=image/jpeg'

Curl (ad image -> JPEG stream):
  curl -X POST 'http://localhost:8000/v1/ad-image?return=image' \
    -F 'input_image=@./person.png;type=image/png' \
    -F 'user_prompt=비 오는 골목, 네온사인 느낌의 감성 배경' \
    -F 'resize_mode=pad' \
    -F 'ratio=4:5' \
    -F 'base_size=768' \
    -F 'elements_json=[{"type":"bg_text","text":"피자킹","font":"","size":64,"color":"white","bg_color":"red","position":"top-center"}]' \
    --output result.jpg

Curl (ad image -> JSON(base64)):
  curl -X POST 'http://localhost:8000/v1/ad-image?return=json' \
    -F 'input_image=@./person.png;type=image/png' \
    -F 'user_prompt=따뜻한 석양의 해변 배경' \
    -F 'ratio=16:9' \
    -F 'base_size=640' \
    -F 'elements_json=[{"type":"text","text":"WEEKEND SALE","font":"","size":72,"color":"yellow","position":"bottom-center"}]'
"""

import os
import io
import json
import base64
from typing import List, Optional, Tuple

import requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv

from PIL import Image, ImageOps, ImageStat, ImageDraw, ImageFont
import google.generativeai as genai
import torch
from diffusers import StableDiffusionInpaintPipeline
from rembg import remove

# =========================
# 0) 환경 설정
# =========================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
_raw_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
MODEL_ID = _raw_model.split("/")[-1]
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent"

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY가 없습니다. 프로젝트 루트의 .env를 확인하세요.")

# Gemini Python SDK 설정 (ad-image에서 사용)
genai.configure(api_key=GEMINI_API_KEY)

# Torch/디바이스
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

# =========================
# 1) 모델 로딩 (Inpainting)
# =========================
# 큰 모델이라 서버 시작 시 로딩. 실패 시 지연 로딩/예외 처리.
INPAINT_PIPE: Optional[StableDiffusionInpaintPipeline] = None

try:
    INPAINT_PIPE = StableDiffusionInpaintPipeline.from_pretrained(
        "runwayml/stable-diffusion-inpainting", torch_dtype=DTYPE, safety_checker=None
    ).to(DEVICE)
except Exception as e:
    # 필요 시 첫 요청 시 재시도할 수 있도록 None 유지
    print(f"[경고] Inpaint 파이프라인 로딩 실패: {e}")

# =========================
# 2) FastAPI 앱
# =========================
app = FastAPI(
    title="Promo & Ad Image Generator (FastAPI)",
    version="1.0.0",
    description="Gemini REST/SDK + SD Inpaint + rembg 조합 백엔드",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# =========================
# 3) 공용 유틸
# =========================

def files_to_inline_parts(files: Optional[List[UploadFile]]) -> List[dict]:
    parts: List[dict] = []
    if not files:
        return parts
    for f in files:
        try:
            data = f.file.read()
        except Exception:
            data = b""
        if not data:
            continue
        mime = f.content_type or "image/jpeg"
        parts.append({
            "inlineData": {
                "data": base64.b64encode(data).decode("utf-8"),
                "mimeType": mime,
            }
        })
    return parts


def build_promo_prompt(
    *, language: str, mood: str, store_name: str, store_description: Optional[str],
    location_text: Optional[str], latitude: Optional[float], longitude: Optional[float], variants: int
) -> str:
    variants = min(max(variants, 1), 5)
    loc_bits = []
    if location_text:
        loc_bits.append(f"주소/지역: {location_text}")
    if latitude is not None and longitude is not None:
        loc_bits.append(f"좌표: {latitude}, {longitude}")
    loc_line = " / ".join(loc_bits) if loc_bits else "위치 정보 없음"

    return f"""
다음 정보를 참고해서 매장 홍보문구를 만들어줘. 출력은 **{language}**로, 총 {variants}개.
반드시 아래 JSON 스키마 형식 그대로만 반환해.

매장 정보
- 이름: {store_name}
- 톤/무드: {mood}
- 설명: {store_description or "없음"}
- {loc_line}
- 첨부 이미지: 매장/메뉴 사진 (문맥에 자연스럽게 반영)

반환 형식 (JSON만, 코드펜스/문장 금지)
{{
  "variants": [
    {{
      "headline": "짧은 한 줄 헤드라인",
      "body": "2~4문장 본문. 매장/메뉴 특징과 위치 맥락을 반영.",
      "tags": ["#해시태그", "#지역", "#메뉴"],
      "cta": "방문/예약/주문을 유도하는 한 문장"
    }}
  ]
}}
""".strip()


def read_image_from_upload(file: UploadFile) -> Image.Image:
    data = file.file.read()
    if not data:
        raise ValueError("빈 파일")
    img = Image.open(io.BytesIO(data)).convert("RGB")
    return img


def resize_image(img: Image.Image, target_width: int, target_height: int, mode: str) -> Image.Image:
    if mode == "crop":
        return ImageOps.fit(img, (target_width, target_height), method=Image.Resampling.LANCZOS)
    # pad
    original_ratio = img.width / img.height
    target_ratio = target_width / target_height
    if original_ratio > target_ratio:
        new_width = target_width
        new_height = int(new_width / original_ratio)
    else:
        new_height = target_height
        new_width = int(new_height * original_ratio)
    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    fill_color = tuple(int(v) for v in ImageStat.Stat(img.convert("RGB")).mean)
    new_img = Image.new("RGB", (target_width, target_height), fill_color)
    paste_x = (target_width - new_width) // 2
    paste_y = (target_height - new_height) // 2
    new_img.paste(resized_img, (paste_x, paste_y))
    return new_img


def get_position_coords(position_str: str, img_width: int, img_height: int, margin: int = 30) -> Tuple[int, int]:
    y_map = {"top": margin, "center": img_height // 2, "bottom": img_height - margin}
    x_map = {"left": margin, "center": img_width // 2, "right": img_width - margin}
    parts = (position_str or "center-center").split("-")
    y_pos = (parts[0] if len(parts) >= 1 else "center").strip()
    x_pos = (parts[1] if len(parts) >= 2 else "center").strip()
    return (x_map.get(x_pos, img_width // 2), y_map.get(y_pos, img_height // 2))


def draw_text_with_background(draw: ImageDraw.ImageDraw, element: dict, font: ImageFont.FreeTypeFont, img_width: int, img_height: int):
    x, y = get_position_coords(element.get("position", "center-center"), img_width, img_height)
    text = element.get("text", "")
    padding, radius = 15, 20
    text_bbox = draw.textbbox((x, y), text, font=font, anchor="mm")
    rect_x0, rect_y0, rect_x1, rect_y1 = (
        text_bbox[0] - padding,
        text_bbox[1] - padding,
        text_bbox[2] + padding,
        text_bbox[3] + padding,
    )
    draw.rounded_rectangle(
        [rect_x0, rect_y0, rect_x1, rect_y1],
        radius=radius,
        fill=element.get("bg_color", "red"),
    )
    draw.text((x, y), text, font=font, fill=element.get("color", "white"), anchor="mm")


def parse_ratio_and_size(ratio: Optional[str], base_size: Optional[int]) -> Tuple[int, int]:
    # ratio like "4:5"; base_size is the shorter side target
    if not ratio:
        ratio = "1:1"
    try:
        w, h = map(int, ratio.split(":"))
        target_ratio = max(1, w) / max(1, h)
    except Exception:
        target_ratio = 1.0
    if not base_size:
        base_size = 512
    if target_ratio >= 1:
        target_height = base_size
        target_width = int(base_size * target_ratio)
    else:
        target_width = base_size
        target_height = int(base_size / target_ratio)
    # SD는 8 배수 권장
    target_width -= (target_width % 8)
    target_height -= (target_height % 8)
    return target_width, target_height


# =========================
# 4) 라우트
# =========================
@app.get("/health")
def health():
    return {"ok": True, "model": MODEL_ID, "device": DEVICE}


@app.get("/")
def index():
    return {
        "message": "Promo & Ad Image backend is running.",
        "endpoints": [
            "/health",
            "/v1/generate-promo (POST form-data)",
            "/v1/ad-image (POST form-data; return=image|json)",
        ],
        "docs": "/docs",
    }


# ---- (A) Promo 텍스트 생성 (Gemini REST) ----
@app.post("/v1/generate-promo")
def generate_promo(
    debug: int = Query(0, description="1이면 모델 호출 없이 더미 반환"),
    store_name: str = Form(...),
    mood: str = Form(...),
    store_description: Optional[str] = Form(None),
    location_text: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    variants: int = Form(3),
    language: str = Form("ko"),
    store_images: Optional[List[UploadFile]] = File(None),
    food_images: Optional[List[UploadFile]] = File(None),
):
    if debug == 1:
        return JSONResponse({
            "variants": [{
                "headline": f"{store_name} — {mood} 톤",
                "body": "디버그 응답입니다. 엔드포인트 연결만 점검합니다.",
                "tags": ["#debug", "#fastapi"],
                "cta": "지금 바로 방문해 보세요",
            }]
        })

    prompt = build_promo_prompt(
        language=language, mood=mood, store_name=store_name,
        store_description=store_description, location_text=location_text,
        latitude=latitude, longitude=longitude, variants=variants,
    )
    parts: List[dict] = [{"text": prompt}]
    parts += files_to_inline_parts(store_images)
    parts += files_to_inline_parts(food_images)

    url = f"{GEMINI_ENDPOINT}?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": parts}]}

    try:
        r = requests.post(url, headers={"Content-Type": "application/json"}, json=payload, timeout=90)
        r.raise_for_status()
        resp_json = r.json()
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="LLM 호출 타임아웃(90s)")
    except requests.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"LLM HTTP 오류: {e.response.status_code} {e.response.text[:300]}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 호출 실패: {repr(e)}")

    raw = ""
    try:
        cands = resp_json.get("candidates", [])
        if cands:
            parts_out = cands[0].get("content", {}).get("parts", [])
            raw = "".join(p.get("text", "") for p in parts_out).strip()
    except Exception:
        pass

    if not raw:
        raise HTTPException(status_code=502, detail="모델 응답이 비어 있습니다.")

    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()

    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict) or "variants" not in parsed:
            raise ValueError("variants 키 없음")
        return JSONResponse(parsed)
    except Exception:
        return JSONResponse({"raw": raw})


# ---- (B) 광고 이미지 생성 (SD Inpaint + rembg + Gemini SDK) ----
@app.post("/v1/ad-image")
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
    # Inpaint 파이프라인 준비 확인
    global INPAINT_PIPE
    if INPAINT_PIPE is None:
        try:
            INPAINT_PIPE = StableDiffusionInpaintPipeline.from_pretrained(
                "runwayml/stable-diffusion-inpainting", torch_dtype=DTYPE, safety_checker=None
            ).to(DEVICE)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Inpaint 파이프라인 로딩 실패: {e}")

    # 입력 이미지 로드
    try:
        ref_image = read_image_from_upload(input_image)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"입력 이미지 오류: {e}")

    # 크기 계산 & 리사이즈
    target_w, target_h = parse_ratio_and_size(ratio, base_size)
    ref_resized = resize_image(ref_image, target_w, target_h, resize_mode)

    # 전경/배경 마스크 생성 (사람/주 피사체를 보호하고 배경만 재생성)
    try:
        foreground_mask = remove(ref_resized, only_mask=True)  # 흰색=전경
        background_mask = ImageOps.invert(foreground_mask)     # 흰색=배경
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"마스크 생성 실패: {e}")

    # Gemini로 배경 프롬프트 보조 생성 (영문 상세 프롬프트)
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        final_prompt = (
            "You are an expert prompt engineer for Stable Diffusion Inpainting.\n"
            "Return ONLY a single concise English prompt that vividly describes a NEW BACKGROUND matching the user's concept.\n"
            "Do NOT mention text, logos, watermarks, or people. Focus on atmosphere, lighting, environment, and style.\n"
            f"User concept (Korean allowed): {user_prompt}\n"
        )
        # 이미지 컨텍스트를 함께 제공 (선택)
        # SDK는 이미지 파트로 PIL을 직접 받지 않으니 바이트로 변환
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
        # 폴백 프롬프트
        generated_prompt = (
            "cinematic wide background, moody atmosphere, soft volumetric lighting, "+
            "depth of field, photorealistic, rich textures, high detail"
        )
        print(f"[경고] Gemini 보조 프롬프트 실패 → 기본 프롬프트 사용: {e}")

    # Inpainting 수행
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

    # 요소 그리기 (텍스트/배경텍스트/로고)
    draw = ImageDraw.Draw(gen_img)
    W, H = gen_img.size

    # 로고 핸들링: 업로드된 logos를 메모리에 로드
    loaded_logos: List[Image.Image] = []
    if logos:
        for lf in logos:
            try:
                loaded_logos.append(Image.open(io.BytesIO(lf.file.read())).convert("RGBA"))
            except Exception:
                loaded_logos.append(None)  # 자리 유지

    # elements_json 파싱
    elements: List[dict] = []
    if elements_json:
        try:
            elements = json.loads(elements_json)
            if not isinstance(elements, list):
                raise ValueError("elements_json은 배열이어야 합니다.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"elements_json 파싱 오류: {e}")

    def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
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
                scale = float(el.get("scale", 0.2))  # 폭 기준 비율
                if 0 <= idx < len(loaded_logos) and loaded_logos[idx] is not None:
                    logo_img = loaded_logos[idx]
                    logo_w = max(1, int(W * max(0.05, min(0.8, scale))))
                    logo_h = max(1, int(logo_w / logo_img.width * logo_img.height))
                    logo_resized = logo_img.resize((logo_w, logo_h), Image.Resampling.LANCZOS)
                    x, y = get_position_coords(el.get("position", "bottom-right"), W, H)
                    lx, ly = int(x - logo_w / 2), int(y - logo_h / 2)
                    gen_img.paste(logo_resized, (lx, ly), logo_resized)
        except Exception as e:
            # 개별 요소 실패는 전체 실패로 보지 않음
            print(f"[요소 경고] 요소 적용 실패: {e}")

    # 반환
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
