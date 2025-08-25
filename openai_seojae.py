import os
import re
from dotenv import load_dotenv
from PIL import Image
from openai import OpenAI
import google.generativeai as genai
import requests
from io import BytesIO
from rembg import remove
from fastapi import APIRouter, Form, File, UploadFile, HTTPException
from fastapi.responses import FileResponse

# -----------------------------
# 1) 환경 설정
# -----------------------------
load_dotenv(".env")

try:
    openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError as e:
    raise SystemExit(f"{e.args[0]}를 .env 파일에서 찾을 수 없습니다. 파일을 확인해주세요.")

# 서버에 이미지를 저장할 디렉터리 설정
IMG_DIR = os.getenv("IMAGE_DIR", "generated_images")

# -----------------------------
# 유틸리티 함수
# -----------------------------
def _clamp_prompt(p: str, maxlen: int = 950) -> str:
    """DALL·E 프롬프트 길이를 1000자 미만으로 안전하게 제한합니다."""
    p = re.sub(r"\s+", " ", (p or "")).strip()
    return p[:maxlen].rstrip()

def _ensure_dir(path: str) -> None:
    """디렉터리가 없으면 생성합니다."""
    os.makedirs(path, exist_ok=True)

def _next_index(save_dir: str) -> int:
    """디렉터리 내 파일들을 스캔하여 다음 파일 번호를 결정합니다."""
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
# 2) 이미지 아웃페인팅 핵심 함수
# -----------------------------
def outpaint_image(input_path, user_prompt_kr, output_path, target_size=1024, target_ratio=1.0):
    """이미지 처리의 모든 단계를 수행하는 메인 함수입니다."""
    temp_canvas_path = "temp_canvas_for_api.png"

    try:
        img = Image.open(input_path)
    except Exception as e:
        print(f"오류: 이미지를 여는 중 문제가 발생했습니다 - {e}")
        return

    # --- 1. Gemini를 사용해 한글 프롬프트를 영어로 변환 및 강화 ---
    print(f"\nGemini가 '{user_prompt_kr}' 컨셉을 최고의 영어 프롬프트로 변환 중...")
    prompt_enhancement_instruction = f"""
    You are a professional food photographer and a DALL-E prompt expert.
    Translate the Korean request into a vivid English prompt for an image outpainting task.
    **VERY IMPORTANT**: The user wants a minimalist scene with ONLY the main food item.
    Your final prompt MUST explicitly command to exclude other objects. Use strong negative keywords.
    For example, add phrases like "Minimalist, clean, no other objects, no cutlery, no spoons, no forks, no glasses, no side dishes, no clutter, plain background."
    **Crucially, the final English prompt must be under 1000 characters.**
    Korean Request: "{user_prompt_kr}"
    Enhanced English Prompt for DALL-E:
    """
    try:
        gemini_model = genai.GenerativeModel("gemini-1.5-flash-latest")
        response = gemini_model.generate_content(prompt_enhancement_instruction)
        generated_prompt_en = response.text.strip()
        if not generated_prompt_en: raise ValueError("Gemini returned an empty prompt.")
    except Exception as e:
        print(f"Gemini 오류 발생, 기본 프롬프트를 사용합니다: {e}")
        generated_prompt_en = f"A high-quality, realistic photograph with: {user_prompt_kr}, minimalist, no other objects."
    
    generated_prompt_en = _clamp_prompt(generated_prompt_en)
    print(f"Gemini 변환 완료:\n   -> {generated_prompt_en}")

    # --- 2. 원본 이미지에서 배경 제거 ---
    print("\n원본 이미지에서 배경을 자동으로 제거합니다...")
    try:
        img_no_bg = remove(img)
    except Exception as e:
        print(f"배경 제거 중 오류가 발생했습니다: {e}")
        return

    # --- 3. 피사체를 캔버스보다 작게 자동 축소 ---
    print("피사체 크기를 아웃페인팅에 적합하게 조절합니다...")
    scale_factor = 0.6
    max_size = int(target_size * scale_factor)
    img_no_bg.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    
    # --- 4. 캔버스에 배치 및 OpenAI API 호출 ---
    canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    img_w, img_h = img_no_bg.size
    center_x, center_y = (target_size - img_w) // 2, (target_size - img_h) // 2
    canvas.paste(img_no_bg, (center_x, center_y), img_no_bg)
    
    print("\nOpenAI DALL-E 2 모델로 아웃페인팅 요청 중...")
    try:
        canvas.save(temp_canvas_path, "PNG")
        with open(temp_canvas_path, "rb") as image_file:
            response = openai_client.images.edit(
                model="dall-e-2", image=image_file, prompt=generated_prompt_en,
                size=f"{target_size}x{target_size}", n=1
            )
        gen_img = Image.open(BytesIO(requests.get(response.data[0].url).content))
    except Exception as e:
        print(f"OpenAI API 호출 중 오류가 발생했습니다: {e}"); return
    finally:
        if os.path.exists(temp_canvas_path): os.remove(temp_canvas_path)

    # --- 5. 최종 비율로 자르기 및 저장 ---
    final_img = gen_img
    if abs(target_ratio - 1.0) > 1e-6:
        w, h = (target_size, int(target_size / target_ratio)) if target_ratio > 1 else (int(target_size * target_ratio), target_size)
        left, top = (target_size - w) // 2, (target_size - h) // 2
        final_img = gen_img.crop((left, top, left + w, top + h))

    final_img.convert("RGB").save(output_path, "JPEG", quality=95)
    print(f"최종 저장 완료 -> {output_path}")

# -----------------------------
# 3) FastAPI 라우터
# -----------------------------
router = APIRouter()

@router.post("/v1/outpaint")
async def outpaint_endpoint(
    input_image: UploadFile = File(..., description="이미지 파일(PNG/JPG)"),
    user_prompt: str = Form(..., description="배경 컨셉 설명(자연어, 한국어 OK)"),
    ratio: str = Form("1:1", description="예: 1:1, 4:5, 16:9"),
):
    _ensure_dir(IMG_DIR)

    n = _next_index(IMG_DIR)
    base_name = f"{n}_food"
    input_path  = os.path.join(IMG_DIR, f"{base_name}.jpg")
    output_path = os.path.join(IMG_DIR, f"{base_name}_AI.jpg")

    try:
        img = Image.open(input_image.file).convert("RGB")
        img.save(input_path, "JPEG", quality=95)
        print(f"업로드 저장 완료 -> {input_path}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"업로드 이미지를 저장할 수 없습니다: {e}")

    try:
        w, h = map(int, ratio.split(":")); target_ratio = w / h
    except Exception:
        target_ratio = 1.0

    try:
        outpaint_image(input_path, user_prompt, output_path, target_size=1024, target_ratio=target_ratio)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"아웃페인트 처리 중 오류: {e}")

    if not os.path.exists(output_path):
        raise HTTPException(status_code=502, detail="아웃페인트 결과 파일이 생성되지 않았습니다.")

    return FileResponse(output_path, media_type="image/jpeg", filename=os.path.basename(output_path))
