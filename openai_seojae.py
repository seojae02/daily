from fastapi import APIRouter, UploadFile, Form
from fastapi.responses import FileResponse
import tempfile
import os
from dotenv import load_dotenv
from PIL import Image
from openai import OpenAI
import google.generativeai as genai
import requests
from io import BytesIO
from rembg import remove

# -----------------------------
# 1) 환경 설정
# -----------------------------
load_dotenv("key.env")

try:
    # OpenAI 클라이언트 초기화
    openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    # Gemini 클라이언트 초기화
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError as e:
    raise SystemExit(f"{e.args[0]}를 key.env 파일에서 찾을 수 없습니다. 파일을 확인해주세요.")

# -----------------------------
# 2) 이미지 아웃페인팅 함수
# -----------------------------
def outpaint_image(input_path, user_prompt_kr, output_path, target_size=1024, target_ratio=1.0):
    """
    Gemini로 프롬프트를 강화하고, 원본 배경을 제거한 뒤, OpenAI로 아웃페인팅을 수행합니다.
    """
    temp_canvas_path = "temp_canvas_for_api.png"

    try:
        img = Image.open(input_path)
        img.save("debug_01_opened_image.png")
        print("✅ [디버깅] 'debug_01_opened_image.png' 파일로 원본 이미지를 저장했습니다.")
    except FileNotFoundError:
        print(f"❌ 오류: '{input_path}' 파일을 찾을 수 없습니다.")
        return
    except Exception as e:
        print(f"❌ 오류: 이미지를 여는 중 문제가 발생했습니다 - {e}")
        return

    # --- 1. Gemini를 사용해 한글 프롬프트를 영어로 변환 및 강화 ---
    print(f"\n🤖 Gemini가 '{user_prompt_kr}' 컨셉을 최고의 영어 프롬프트로 변환 중...")
    # [수정된 부분] DALL-E가 다른 물체를 추가하지 못하도록 지시를 훨씬 더 강력하게 수정
    prompt_enhancement_instruction = f"""
    You are a professional food photographer and a DALL-E prompt expert.
    Translate the Korean request into a vivid English prompt for an image outpainting task.
    The goal is to fill the background around a main food subject.
    Describe the background, texture, and lighting for a high-quality photo.

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
        print(f"✅ Gemini 변환 완료 (길이: {len(generated_prompt_en)}자):\n   -> {generated_prompt_en}")
    except Exception as e:
        print(f"⚠️ Gemini 오류 발생, 기본 프롬프트를 사용합니다: {e}")
        generated_prompt_en = f"A high-quality, realistic photograph with a background of: {user_prompt_kr}, minimalist, no other objects, no cutlery."

    # --- 2. 원본 이미지에서 배경 제거 ---
    print("\n✨ 원본 이미지에서 배경을 자동으로 제거합니다...")
    try:
        img_no_bg = remove(img)
        img_no_bg.save("debug_02_no_bg_image.png")
        print("✅ [디버깅] 'debug_02_no_bg_image.png' 파일로 배경 제거된 이미지를 저장했습니다.")
    except Exception as e:
        print(f"⚠️ 배경 제거 중 오류가 발생했습니다: {e}")
        return

    # --- 3. 배경 제거된 이미지를 캔버스에 배치 ---
    canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    img_w, img_h = img_no_bg.size
    center_x, center_y = (target_size - img_w) // 2, (target_size - img_h) // 2
    canvas.paste(img_no_bg, (center_x, center_y), img_no_bg)
    
    print("\n🎨 OpenAI DALL-E 2 모델로 아웃페인팅 요청 중...")
    try:
        canvas.save(temp_canvas_path, "PNG")
        with open(temp_canvas_path, "rb") as image_file:
            response = openai_client.images.edit(
                model="dall-e-2",
                image=image_file,
                prompt=generated_prompt_en, # Gemini가 만든 영어 프롬프트 사용
                size=f"{target_size}x{target_size}",
                n=1
            )
        
        image_url = response.data[0].url
        response_img = requests.get(image_url)
        gen_img = Image.open(BytesIO(response_img.content))

    except Exception as e:
        print(f"⚠️ OpenAI API 호출 중 오류가 발생했습니다: {e}")
        return
    finally:
        if os.path.exists(temp_canvas_path):
            os.remove(temp_canvas_path)

    # --- 4. 최종 비율로 이미지 자르기 ---
    final_img = gen_img
    if abs(target_ratio - 1.0) > 1e-6:
        if target_ratio > 1:
            final_h = int(target_size / target_ratio)
            final_w = target_size
        else:
            final_w = int(target_size * target_ratio)
            final_h = target_size
            
        left = (target_size - final_w) // 2
        top = (target_size - final_h) // 2
        right = left + final_w
        bottom = top + final_h
        
        final_img = gen_img.crop((left, top, right, bottom))

    final_img.convert("RGB").save(output_path, "JPEG", quality=95)
    print(f"\n✅ 작업 완료! '{output_path}' 경로에 이미지가 저장되었습니다.")

# -----------------------------
# -----------------------------
# 3) 메인 실행 부분
# -----------------------------

# FastAPI 라우터 추가
router = APIRouter()

@router.post("/v1/outpaint")
async def outpaint_endpoint(
    input_image: UploadFile = Form(...),
    user_prompt: str = Form(...),
    ratio: str = Form("1:1"),
    size: int = Form(1024)
):
    # 임시 파일로 저장
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_in:
        temp_in.write(await input_image.read())
        temp_in_path = temp_in.name

    try:
        w, h = map(int, ratio.split(":"))
        target_ratio = w / h
    except Exception:
        target_ratio = 1.0

    output_path = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False).name

    outpaint_image(temp_in_path, user_prompt, output_path, target_size=size, target_ratio=target_ratio)
    return FileResponse(output_path, media_type="image/jpeg")
