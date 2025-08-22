import os
from io import BytesIO
from dotenv import load_dotenv
from PIL import Image, ImageOps, ImageStat, ImageDraw, ImageFont
import google.generativeai as genai
import torch
from diffusers import StableDiffusionInpaintPipeline
from rembg import remove


# -----------------------------
# 0) 유틸 함수들
# -----------------------------
def resize_image(
    img: Image.Image, target_width: int, target_height: int, mode: str
) -> Image.Image:
    """이미지를 목표 해상도에 맞게 'pad' 또는 'crop' 방식으로 리사이즈합니다."""
    if mode == "crop":
        return ImageOps.fit(
            img, (target_width, target_height), method=Image.Resampling.LANCZOS
        )
    else:  # pad mode
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


def get_position_coords(position_str, img_width, img_height, margin=30):
    y_map = {"top": margin, "center": img_height / 2, "bottom": img_height - margin}
    x_map = {"left": margin, "center": img_width / 2, "right": img_width - margin}
    parts = position_str.split("-")
    y_pos = parts[0]
    x_pos = parts[1] if len(parts) > 1 else "center"
    return (x_map.get(x_pos, img_width / 2), y_map.get(y_pos, img_height / 2))


def draw_text_with_background(draw, element, font, img_width, img_height):
    x, y = get_position_coords(element["position"], img_width, img_height)
    text = element["text"]
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


# -----------------------------
# 1) 환경 변수 및 모델 설정
# -----------------------------
print("환경 설정 및 모델 로딩을 시작합니다...")
load_dotenv("key.env")
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise SystemExit("GEMINI_API_KEY를 찾을 수 없습니다.")
genai.configure(api_key=API_KEY)
device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32
print(f"\nStable Diffusion Inpainting 모델 로딩 중... (디바이스: {device})")
pipe = StableDiffusionInpaintPipeline.from_pretrained(
    "runwayml/stable-diffusion-inpainting", torch_dtype=dtype, safety_checker=None
).to(device)
print("✅ 모델 로딩 완료!")


# -----------------------------
# 2) 이미지 생성 함수 정의
# -----------------------------
def generate_ad_image(
    input_path, user_prompt, output_path, target_width, target_height, mode, elements
):
    try:
        ref_image = Image.open(input_path).convert("RGB")
    except FileNotFoundError:
        print(f"❌ 오류: '{input_path}' 파일을 찾을 수 없습니다.")
        return

    print(
        f"\n📏 이미지를 {target_width}x{target_height} 크기, '{mode}' 방식으로 리사이즈합니다..."
    )
    ref_image_resized = resize_image(ref_image, target_width, target_height, mode)

    print("\n🔬 핵심 피사체 분석 및 마스크 생성 중...")
    foreground_mask = remove(ref_image_resized, only_mask=True)
    background_mask = ImageOps.invert(foreground_mask)
    print("✅ 마스크 생성 완료!")

    role_definition = "You are an expert prompt engineer for Stable Diffusion."
    final_gemini_prompt = f'User\'s request: "{user_prompt}"\nBased on the request, create a detailed, specific English prompt for Stable Diffusion Inpainting. Focus ONLY on describing the new background. The main subject is masked and will not be changed.'
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        gemini_response = model.generate_content(
            [final_gemini_prompt, ref_image_resized]
        )
        generated_prompt = (gemini_response.text or "").strip()
        if not generated_prompt:
            raise ValueError("빈 프롬프트가 반환되었습니다.")
        print(f"\n🤖 Gemini 프롬프트:\n{generated_prompt}")
    except Exception as e:
        print(f"⚠️ Gemini 오류, 대체 프롬프트를 사용합니다: {e}")
        generated_prompt = "A cinematic advertising photo, luxury background, soft studio lighting, rim light, bokeh"

    print("\n🎨 배경 생성 중 (Inpainting)...")
    with torch.no_grad():
        out = pipe(
            prompt=generated_prompt,
            image=ref_image_resized,
            mask_image=background_mask,
            width=target_width,
            height=target_height,
            guidance_scale=7.5,
            num_inference_steps=50,
            # --- Negative Prompt 수정됨 ---
            negative_prompt="text, logo, watermark, blurry, low quality, distorted, bad quality, clutter, objects, texture, pattern, gradient, light, reflections, surface",
        )
    gen_img = out.images[0]

    print("\n✍️ 텍스트 및 로고 추가 작업 시작...")
    draw = ImageDraw.Draw(gen_img)
    img_width, img_height = gen_img.size

    for element in elements:
        try:
            if element["type"] in ["text", "bg_text"]:
                font = ImageFont.truetype(element["font"], element["size"])
                if element["type"] == "text":
                    x, y = get_position_coords(
                        element["position"], img_width, img_height
                    )
                    draw.text(
                        (x, y),
                        element["text"],
                        font=font,
                        fill=element["color"],
                        anchor="mm",
                    )
                else:
                    draw_text_with_background(
                        draw, element, font, img_width, img_height
                    )
            elif element["type"] == "logo":
                logo_img = Image.open(element["path"]).convert("RGBA")
                logo_width = int(img_width * 0.2)
                logo_height = int(logo_width / logo_img.width * logo_img.height)
                logo_img = logo_img.resize(
                    (logo_width, logo_height), Image.Resampling.LANCZOS
                )
                x, y = get_position_coords(element["position"], img_width, img_height)
                logo_x, logo_y = int(x - logo_width / 2), int(y - logo_height / 2)
                gen_img.paste(logo_img, (logo_x, logo_y), logo_img)
        except Exception as e:
            print(f"⚠️ 요소 추가 중 오류 발생: {e}")

    gen_img.save(output_path, quality=95)
    print(f"\n✅ 완료: '{output_path}' 로 저장되었습니다.")


# -----------------------------
# 3) 대화형 루프 실행
# -----------------------------
if __name__ == "__main__":
    while True:
        print("\n" + "=" * 50)
        input_image_path = input("▶️ 이미지 파일 경로: ")
        if not input_image_path:
            break

        resize_mode = input("▶️ 리사이즈 방식 ('pad' 또는 'crop'): ").lower()
        if resize_mode not in ["pad", "crop"]:
            resize_mode = "pad"

        ratio_str = input("▶️ 사진 비율 (예: 1:1, 4:5, 16:9): ")
        try:
            w, h = map(int, ratio_str.split(":"))
            target_ratio = w / h
        except:
            print("⚠️ 잘못된 형식. 1:1 사용.")
            target_ratio = 1.0

        try:
            base_size = int(input("▶️ 사진의 짧은 쪽 기준 크기 (예: 768, 기본값 512): "))
        except ValueError:
            base_size = 512

        if target_ratio >= 1:
            target_height = base_size
            target_width = int(base_size * target_ratio)
        else:
            target_width = base_size
            target_height = int(base_size / target_ratio)

        target_width = target_width - (target_width % 8)
        target_height = target_height - (target_height % 8)
        print(f"   -> 최종 생성 크기: {target_width}x{target_height}")

        user_prompt_text = input("▶️ 배경 컨셉: ")
        if not user_prompt_text:
            break

        elements_to_add = []
        default_font_path = "C:\\Users\\seo12\\OneDrive\\Desktop\\daily\\nanum-barun-gothic\\NanumBarunGothic.ttf"

        while True:
            print("\n--- 요소 추가 ---")
            choice = input(
                "1: 텍스트, 2: 배경있는 텍스트, 3: 로고, 4: 완료\n▶️ 추가할 요소 타입: "
            )
            if choice == "4":
                break
            element = {}
            try:
                if choice in ["1", "2"]:
                    element["type"] = "text" if choice == "1" else "bg_text"
                    element["text"] = input("  - 내용: ")
                    font_path = input(f"  - 폰트 경로 (기본값 Enter): ")
                    element["font"] = font_path if font_path else default_font_path
                    element["size"] = int(input("  - 크기 (예: 60): "))
                    element["color"] = input("  - 색상 (예: white): ")
                    element["position"] = input("  - 위치 (예: top-center): ").lower()
                    if choice == "2":
                        element["bg_color"] = input("  - 배경 색상 (예: red): ")
                elif choice == "3":
                    element["type"] = "logo"
                    element["path"] = input("  - 로고 파일 경로: ")
                    element["position"] = input(
                        "  - 위치 (예: bottom-center): "
                    ).lower()
                else:
                    print("⚠️ 잘못된 선택입니다.")
                    continue
                elements_to_add.append(element)
            except ValueError:
                print("⚠️ 잘못된 값입니다. 다시 입력해주세요.")

        base_name = os.path.basename(input_image_path).split(".")[0]
        output_base = f"result_{base_name}_final"
        counter = 1
        output_filename = f"{output_base}_{counter}.jpg"
        while os.path.exists(output_filename):
            counter += 1
            output_filename = f"{output_base}_{counter}.jpg"

        print(f"\n💾 결과물은 '{output_filename}' 이름으로 저장됩니다.")
        generate_ad_image(
            input_image_path,
            user_prompt_text,
            output_filename,
            target_width,
            target_height,
            resize_mode,
            elements_to_add,
        )

        print("\n" + "=" * 50)
        another = input("계속해서 다른 이미지를 만드시겠습니까? (y/n): ").lower()
        if another != "y":
            break

    print("프로그램을 종료합니다.")
