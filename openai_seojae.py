# openai_seojae.py

import os
import re
from io import BytesIO

from dotenv import load_dotenv
from PIL import Image
from rembg import remove
import requests

from fastapi import APIRouter, Form, File, UploadFile, HTTPException, Response
from openai import OpenAI
import google.generativeai as genai

# -----------------------------
# 1) 환경 설정
# -----------------------------
load_dotenv(".env")

try:
    openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError as e:
    raise SystemExit(f"{e.args[0]}를 .env 파일에서 찾을 수 없습니다. 파일을 확인해주세요.")

# 서버에 이미지를 저장할 디렉터리 (컨테이너 실행 시 -e IMAGE_DIR=... 로 덮어쓰기 가능)
IMG_DIR = os.getenv("IMAGE_DIR", "generated_images")


# -----------------------------
# 2) 유틸리티 함수
# -----------------------------
def _clamp_prompt(p: str, maxlen: int = 950) -> str:
    """프롬프트를 1000자 제한 이하로 클램프"""
    p = re.sub(r"\s+", " ", (p or "")).strip()
    return p[:maxlen].rstrip()


def _ensure_dir(path: str) -> None:
    """디렉터리가 없으면 생성"""
    os.makedirs(path, exist_ok=True)


def _next_index(save_dir: str) -> int:
    """폴더 내에서 (N)_food(.AI).jpg 패턴을 스캔해 다음 번호를 리턴"""
    pat = re.compile(r"^(\d+)_food(_AI)?\.jpg$", re.IGNORECASE)
    max_n = 0
    try:
        for name in os.listdir(save_dir):
            m = pat.match(name)
            if m:
                n = int(m.group(1))
                if n > max_n:
                    max_n = n
    except FileNotFoundError:
        pass
    return max_n + 1


# -----------------------------
# 3) 이미지 아웃페인팅 함수
# -----------------------------
def outpaint_image(input_path, user_prompt_kr, output_path, target_size=1024, target_ratio=1.0):
    """이미지 아웃페인팅 전체 파이프라인"""
    temp_canvas_path = "temp_canvas_for_api.png"

    # 입력 이미지 열기
    try:
        img = Image.open(input_path)
    except Exception as e:
        print(f"❌ 입력 이미지 오류: {e}")
        return

    # Gemini 프롬프트 강화
    prompt_instruction = f"""
    You are a professional food photographer and a DALL-E prompt expert.
    Translate the Korean request into a vivid English prompt for an image outpainting task.
    Minimalist, clean, ONLY the main food item, plain background. 
    No other objects, no cutlery, no side dishes.
    Korean Request: "{user_prompt_kr}"
    """
    try:
        gemini_model = genai.GenerativeModel("gemini-1.5-flash-latest")
        resp = gemini_model.generate_content(prompt_instruction)
        generated_prompt_en = (resp.text or "").strip()
        if not generated_prompt_en:
            raise ValueError("Gemini returned empty")
    except Exception as e:
        print(f"⚠️ Gemini 오류: {e}")
        generated_prompt_en = f"A minimalist food photo with {user_prompt_kr}, no other objects, plain background."
    generated_prompt_en = _clamp_prompt(generated_prompt_en)

    # 배경 제거
    try:
        img_no_bg = remove(img)
    except Exception as e:
        print(f"⚠️ 배경 제거 오류: {e}")
        return

    # 피사체 축소 후 캔버스 배치
    scale_factor = 0.6
    img_no_bg.thumbnail((int(target_size * scale_factor), int(target_size * scale_factor)), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    iw, ih = img_no_bg.size
    canvas.paste(img_no_bg, ((target_size - iw) // 2, (target_size - ih) // 2), img_no_bg)

    # OpenAI DALL·E 아웃페인팅 호출
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

    # 최종 크롭
    final_img = gen_img
    if abs(target_ratio - 1.0) > 1e-6:
        if target_ratio > 1:
            w, h = (target_size, int(target_size / target_ratio))
        else:
            w, h = (int(target_size * target_ratio), target_size)
        left, top = (target_size - w) // 2, (target_size - h) // 2
        final_img = gen_img.crop((left, top, left + w, top + h))

    # 저장
    final_img.convert("RGB").save(output_path, "JPEG", quality=95)
    print(f"✅ 최종 저장 완료 → {output_path}")


# -----------------------------
# 4) FastAPI 라우터
# -----------------------------
router = APIRouter()

@router.post(
    "/v1/outpaint",
    status_code=204,
    responses={
        204: {"description": "Image saved successfully (no content)"},
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"},
        502: {"description": "Processing error"},
    },
)
async def outpaint_endpoint(
    input_image: UploadFile = File(..., description="이미지 파일(PNG/JPG)"),
    user_prompt: str = Form(..., description="배경 컨셉 설명 (한국어 OK)"),
    ratio: str = Form("1:1", description="예: 1:1, 4:5, 16:9"),
):
    """
    - 입력 저장: {IMG_DIR}/{N}_food.jpg
    - 결과 저장: {IMG_DIR}/{N}_food_AI.jpg
    - 응답은 본문 없이 204 No Content
    """
    _ensure_dir(IMG_DIR)

    n = _next_index(IMG_DIR)
    base = f"{n}_food"
    input_path = os.path.join(IMG_DIR, f"{base}.jpg")
    output_path = os.path.join(IMG_DIR, f"{base}_AI.jpg")

    # 원본 저장
    try:
        img = Image.open(input_image.file).convert("RGB")
        img.save(input_path, "JPEG", quality=95)
        print(f"✅ 업로드 저장 완료 → {input_path}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"업로드 이미지 저장 실패: {e}")

    # 비율 파싱
    try:
        w, h = map(int, ratio.split(":"))
        target_ratio = w / h
    except Exception:
        target_ratio = 1.0

    # 아웃페인트 실행
    try:
        outpaint_image(input_path, user_prompt, output_path, target_size=1024, target_ratio=target_ratio)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"아웃페인트 실패: {e}")

    if not os.path.exists(output_path):
        raise HTTPException(status_code=502, detail="결과 파일이 생성되지 않았습니다.")

    # 아무것도 반환하지 않음
    return Response(status_code=204)