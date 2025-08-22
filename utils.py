import base64
import io
import json
from typing import List, Optional, Tuple
from fastapi import UploadFile
from PIL import Image, ImageOps, ImageStat, ImageDraw, ImageFont

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

def build_promo_prompt(language: str, mood: str, store_name: str, store_description: Optional[str], location_text: Optional[str], latitude: Optional[float], longitude: Optional[float], variants: int) -> str:
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
    target_width -= (target_width % 8)
    target_height -= (target_height % 8)
    return target_width, target_height
