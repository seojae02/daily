from fastapi import APIRouter, Form, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
import os
import re
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
load_dotenv(".env")

try:
    openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except KeyError as e:
    raise SystemExit(f"{e.args[0]}를 .env 파일에서 찾을 수 없습니다. 파일을 확인해주세요.")

# 마운트된 서버 저장 디렉터리 (없으면 기본값)
IMG_DIR = os.getenv("IMAGE_DIR", "/home/ec2-user/BE/img")

# -----------------------------
# 유틸: 프롬프트 길이/공백 정리
# -----------------------------
def _clamp_prompt(p: str, maxlen: int = 950) -> str:
    """
    DALL·E 프롬프트는 1000자 제한 → 안전하게 950자로 클램프.
    연속 공백/개행을 한 칸으로 정리한 뒤 자른다.
    """
    p = re.sub(r"\s+", " ", (p or "")).strip()
    return p[:maxlen].rstrip()

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _next_index(save_dir: str) -> int:
    """
    save_dir 안의 파일들 중 `(\d+)_food(.AI)?\.jpg` 패턴을 찾아
    가장 큰 번호 + 1을 반환. 없으면 1.
    """
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
# 2) 이미지 아웃페인팅 함수
# -----------------------------
def outpaint_image(input_path, user_prompt_kr, output_path, target_size=1024, target_ratio=1.0):
    temp_canvas_path = "temp_canvas_for_api.png"

    try:
        img = Image.open(input_path)
        img.save("debug_01_opened_image.png")
        print("✅ 원본 이미지 확인 완료")
    except FileNotFoundError:
        print(f"❌ 오류: '{input_path}' 파일을 찾을 수 없습니다.")
        return
    except Exception as e:
        print(f"❌ 오류: 이미지를 여는 중 문제가 발생했습니다 - {e}")
        return

    # --- Gemini 프롬프트 강화 ---
    prompt_instruction = f"""
    You are a professional food photographer and a DALL-E prompt expert.
    Translate the Korean request into a vivid English prompt for an image outpainting task.
    Minimalist scene, ONLY the main food item, no other objects.

    Korean Request: "{user_prompt_kr}"
    """
    try:
        gemini_model = genai.GenerativeModel("gemini-1.5-flash-latest")
        response = gemini_model.generate_content(prompt_instruction)
        generated_prompt_en = (response.text or "").strip() or f"A minimalist food photo with: {user_prompt_kr}"
    except Exception as e:
        print(f"⚠️ Gemini 오류: {e}")
        generated_prompt_en = f"A minimalist food photo with: {user_prompt_kr}"

    # 프롬프트 길이 제한 적용
    generated_prompt_en = _clamp_prompt(generated_prompt_en, 950)
    print(f"📝 Final prompt length: {len(generated_prompt_en)}")

    # --- 배경 제거 ---
    try:
        img_no_bg = remove(img)
        img_no_bg.save("debug_02_no_bg_image.png")
    except Exception as e:
        print(f"⚠️ 배경 제거 중 오류: {e}")
        return

    # --- 캔버스에 배치 ---
    canvas = Image.new("RGBA", (target_size, target_size), (0, 0, 0, 0))
    img_w, img_h = img_no_bg.size
    center_x, center_y = (target_size - img_w) // 2, (target_size - img_h) // 2
    canvas.paste(img_no_bg, (center_x, center_y), img_no_bg)

    # --- OpenAI DALL-E 아웃페인팅 ---
    try:
        canvas.save(temp_canvas_path, "PNG")
        with open(temp_canvas_path, "rb") as image_file:
            response = openai_client.images.edit(
                model="dall-e-2",
                image=image_file,
                prompt=generated_prompt_en,
                size=f"{target_size}x{target_size}",
                n=1
            )
        image_url = response.data[0].url
        response_img = requests.get(image_url)
        gen_img = Image.open(BytesIO(response_img.content))
    except Exception as e:
        print(f"⚠️ OpenAI API 호출 오류: {e}")
        return
    finally:
        if os.path.exists(temp_canvas_path):
            os.remove(temp_canvas_path)

    # --- 최종 크롭 ---
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
    print(f"✅ 최종 저장 완료 → {output_path}")

# -----------------------------
# 3) FastAPI 라우터
# -----------------------------
router = APIRouter()

@router.post("/v1/outpaint")
async def outpaint_endpoint(
    input_image: UploadFile = File(..., description="이미지 파일(PNG/JPG)"),
    user_prompt: str = Form(..., description="배경 컨셉 설명(자연어, 한국어 OK)"),
    ratio: str = Form("1:1", description="예: 1:1, 4:5, 16:9"),
    size: int = Form(1024, description="짧은 변 기준 크기"),
):
    """
    - 업로드 원본 저장: {IMG_DIR}/{N}_food.jpg
    - 결과 저장: {IMG_DIR}/{N}_food_AI.jpg
    - N은 폴더 내 기존 번호들 중 최대값+1
    """
    _ensure_dir(IMG_DIR)

    # 다음 인덱스 계산
    n = _next_index(IMG_DIR)
    base_name = f"{n}_food"
    input_path  = os.path.join(IMG_DIR, f"{base_name}.jpg")
    output_path = os.path.join(IMG_DIR, f"{base_name}_AI.jpg")  # == {n}_food_AI.jpg

    # 업로드 원본을 서버(마운트 경로)에 저장
    try:
        # 파일 확장자 상관없이 JPEG로 강제 저장(통일)
        img = Image.open(input_image.file).convert("RGB")
        img.save(input_path, "JPEG", quality=95)
        print(f"✅ 업로드 저장 완료 → {input_path}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"업로드 이미지를 저장할 수 없습니다: {e}")

    # 비율 파싱
    try:
        w, h = map(int, ratio.split(":"))
        target_ratio = w / h
    except Exception:
        target_ratio = 1.0

    # 생성 (입력: {n}_food.jpg → 출력: {n}_food_AI.jpg)
    try:
        outpaint_image(input_path, user_prompt, output_path, target_size=size, target_ratio=target_ratio)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"아웃페인트 처리 중 오류: {e}")

    # 결과 확인
    if not os.path.exists(output_path):
        raise HTTPException(status_code=502, detail="아웃페인트 결과 파일이 생성되지 않았습니다.")

    # 생성물 반환 (필요 시 nginx /images/ 에서 URL로 바로 접근 가능)
    return FileResponse(output_path, media_type="image/jpeg", filename=os.path.basename(output_path))