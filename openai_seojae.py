# openai_seojae.py
import os, re
from io import BytesIO
from dotenv import load_dotenv
from PIL import Image
from rembg import remove
import requests

from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Response
from openai import OpenAI
import google.generativeai as genai

load_dotenv(".env")

try:
    openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError as e:
    raise SystemExit(f"{e.args[0]}를 .env 파일에서 찾을 수 없습니다. 파일을 확인해주세요.")

# 루트 저장 경로(마운트): /home/ec2-user/BE/img
IMAGE_ROOT = os.getenv("IMAGE_DIR", "/home/ec2-user/BE/img")
FOOD_DIR   = os.path.join(IMAGE_ROOT, "food")   # 음식 관련 저장소
STORE_DIR  = os.path.join(IMAGE_ROOT, "store")  # 가게 이미지 저장소 (참고용)

def _ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)

def _clamp_prompt(p: str, maxlen: int = 950) -> str:
    p = re.sub(r"\s+", " ", (p or "")).strip()
    return p[:maxlen].rstrip()

def _next_food_index() -> int:
    """
    FOOD_DIR 안의 파일 중 ^(\d+)_food(_AI)?\.jpg 의 최대 번호 + 1
    """
    _ensure_dir(FOOD_DIR)
    pat = re.compile(r"^(\d+)_food(_AI)?\.jpg$", re.IGNORECASE)
    max_n = 0
    for name in os.listdir(FOOD_DIR):
        m = pat.match(name)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return max_n + 1

def outpaint_image(input_path, user_prompt_kr, output_path, target_size=1024, target_ratio=1.0):
    temp_canvas_path = "temp_canvas_for_api.png"
    try:
        img = Image.open(input_path)
    except Exception as e:
        print(f"❌ 입력 이미지 오류: {e}")
        return

    prompt_instruction = f"""
    You are a professional food photographer and a DALL-E prompt expert.
    Translate the Korean request into a vivid English prompt for an image outpainting task.
    VERY IMPORTANT: The user wants a minimalist scene. Your prompt MUST explicitly command to exclude other objects. Use strong negative keywords like "Minimalist, clean, no other objects, no cutlery, no spoons, no forks, no clutter, plain background."
    Crucially, the final English prompt must be under 1000 characters.
    Korean Request: "{user_prompt_kr}"
    """
    try:
        gemini_model = genai.GenerativeModel("gemini-1.5-flash-latest")
        resp = gemini_model.generate_content(prompt_instruction)
        generated_prompt_en = (resp.text or "").strip() or "Minimalist food photo, no other objects, plain background."
    except Exception as e:
        print(f"⚠️ Gemini 오류: {e}")
        generated_prompt_en = "Minimalist food photo, no other objects, plain background."
    generated_prompt_en = _clamp_prompt(generated_prompt_en)

    try:
        img_no_bg = remove(img)
    except Exception as e:
        print(f"⚠️ 배경 제거 오류: {e}")
        return

    scale = 0.6
    img_no_bg.thumbnail((int(target_size*scale), int(target_size*scale)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (target_size, target_size), (0,0,0,0))
    iw, ih = img_no_bg.size
    canvas.paste(img_no_bg, ((target_size - iw)//2, (target_size - ih)//2), img_no_bg)

    try:
        canvas.save(temp_canvas_path, "PNG")
        with open(temp_canvas_path, "rb") as fp:
            r = openai_client.images.edit(
                model="dall-e-2",
                image=fp,
                prompt=generated_prompt_en,
                size=f"{target_size}x{target_size}",
                n=1,
            )
        url = r.data[0].url
        gen_img = Image.open(BytesIO(requests.get(url).content))
    except Exception as e:
        print(f"⚠️ OpenAI API 오류: {e}")
        return
    finally:
        if os.path.exists(temp_canvas_path):
            os.remove(temp_canvas_path)

    final_img = gen_img
    if abs(target_ratio - 1.0) > 1e-6:
        if target_ratio > 1:
            w, h = (target_size, int(target_size/target_ratio))
        else:
            w, h = (int(target_size*target_ratio), target_size)
        left, top = (target_size - w)//2, (target_size - h)//2
        final_img = gen_img.crop((left, top, left+w, top+h))

    final_img.convert("RGB").save(output_path, "JPEG", quality=95)
    print(f"✅ 최종 저장 → {output_path}")

router = APIRouter()

@router.post(
    "/v1/outpaint",
    status_code=204,
    responses={204: {"description": "saved (no content)"}})
async def outpaint_endpoint(
    input_image: UploadFile = File(...),
    user_prompt: str = Form(...),
    ratio: str = Form("1:1"),
):
    _ensure_dir(FOOD_DIR)

    n = _next_food_index()
    base = f"{n}_food"
    input_path  = os.path.join(FOOD_DIR, f"{base}.jpg")
    output_path = os.path.join(FOOD_DIR, f"{base}_AI.jpg")

    try:
        img = Image.open(input_image.file).convert("RGB")
        img.save(input_path, "JPEG", quality=95)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"업로드 저장 실패: {e}")

    try:
        w, h = map(int, ratio.split(":"))
        target_ratio = w/h
    except Exception:
        target_ratio = 1.0

    outpaint_image(input_path, user_prompt, output_path, target_size=1024, target_ratio=target_ratio)
    if not os.path.exists(output_path):
        raise HTTPException(status_code=502, detail="결과 파일 생성 실패")

    return Response(status_code=204)
