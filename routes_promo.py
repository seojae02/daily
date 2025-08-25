# routes_promo.py
from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from typing import List, Optional
import os, re, json, glob, requests

from config import GEMINI_API_KEY, GEMINI_ENDPOINT, MODEL_ID
from utils import build_promo_prompt, filepaths_to_inline_parts, format_body_with_newlines_and_images

router = APIRouter()

IMAGE_ROOT = os.getenv("IMAGE_DIR", "/home/ec2-user/BE/img")
FOOD_DIR   = os.path.join(IMAGE_ROOT, "food")
STORE_DIR  = os.path.join(IMAGE_ROOT, "store")

def _latest_group_with_food_ai() -> Optional[int]:
    """
    FOOD_DIR에서 N_food_AI.jpg 중 가장 큰 N을 반환
    """
    if not os.path.isdir(FOOD_DIR):
        return None
    pat = re.compile(r"^(\d+)_food_AI\.jpg$", re.IGNORECASE)
    max_n = None
    for name in os.listdir(FOOD_DIR):
        m = pat.match(name)
        if m:
            n = int(m.group(1))
            if (max_n is None) or (n > max_n):
                max_n = n
    return max_n

def _build_public_url(request: Request, subdir: str, filename: str) -> str:
    scheme = request.headers.get("X-Forwarded-Proto", request.url.scheme)
    host   = request.headers.get("X-Forwarded-Host", request.headers.get("host", request.url.netloc))
    return f"{scheme}://{host}/images/{subdir}/{filename}"

@router.post("/v1/generate-promo")
def generate_promo(
    request: Request,
    debug: int = Query(0),
    store_name: str = Form(...),
    mood: str = Form(...),
    store_description: Optional[str] = Form(None),
    location_text: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    variants: int = Form(3),
    language: str = Form("ko"),
):
    """
    - 본문 이미지: '가공 음식(food/N_food_AI.jpg)' + '가게 이미지(store/N_store_*.jpg)' 만 사용
    - 원본 음식(food/N_food.jpg)은 본문에 포함하지 않음
    - 본문은 6~8문장 유도
    """
    if debug == 1:
        demo_body = "디버그 응답입니다. 6~8줄 이상 문장 생성과 URL 삽입 포맷만 확인합니다!"
        demo_body = format_body_with_newlines_and_images(demo_body, [])
        return JSONResponse({
            "variants": [{
                "headline": f"{store_name} — {mood} 톤",
                "body": demo_body,
                "tags": ["#debug", "#fastapi"],
                "cta": "지금 바로 방문해 보세요",
            }]
        })

    # 1) 최신 그룹 N 탐색(가공 음식 기준)
    n = _latest_group_with_food_ai()
    food_ai_path = None
    store_img_paths: List[str] = []
    image_urls: List[str] = []

    if n is not None:
        # food: N_food_AI.jpg
        food_ai_candidate = os.path.join(FOOD_DIR, f"{n}_food_AI.jpg")
        if os.path.exists(food_ai_candidate):
            food_ai_path = food_ai_candidate
            image_urls.append(_build_public_url(request, "food", f"{n}_food_AI.jpg"))

        # store: N_store_*.jpg
        store_files = sorted(glob.glob(os.path.join(STORE_DIR, f"{n}_store_*.jpg")))
        for p in store_files:
            store_img_paths.append(p)
            image_urls.append(_build_public_url(request, "store", os.path.basename(p)))

    # 2) 프롬프트
    prompt = build_promo_prompt(
        language=language, mood=mood, store_name=store_name,
        store_description=store_description, location_text=location_text,
        latitude=latitude, longitude=longitude, variants=variants,
    )

    # 3) 모델 입력 parts (텍스트 + 이미지)
    parts: List[dict] = [{"text": prompt}]
    img_for_model: List[str] = []
    img_for_model.extend(store_img_paths)
    if food_ai_path:
        img_for_model.append(food_ai_path)
    parts += filepaths_to_inline_parts(img_for_model)

    # 4) Gemini 호출
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

    # 5) 응답 파싱
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

    # 6) JSON 파싱 + 본문 포맷(문장, \n, 이미지 URL을 모두 공백으로 구분)
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict) or "variants" not in parsed:
            raise ValueError("variants 키 없음")

        if isinstance(parsed.get("variants"), list):
            for v in parsed["variants"]:
                if isinstance(v, dict) and "body" in v:
                    v["body"] = format_body_with_newlines_and_images(
                        v.get("body", ""), image_urls
                    )

        parsed["_images"] = {
            "group": n,
            "food_ai": os.path.basename(food_ai_path) if food_ai_path else None,
            "stores": [os.path.basename(p) for p in store_img_paths],
            "urls": image_urls,
            "roots": {"food": FOOD_DIR, "store": STORE_DIR},
        }
        return JSONResponse(parsed)
    except Exception:
        return JSONResponse({
            "raw": raw,
            "_images": {
                "group": n,
                "food_ai": os.path.basename(food_ai_path) if food_ai_path else None,
                "stores": [os.path.basename(p) for p in store_img_paths],
                "urls": image_urls,
                "roots": {"food": FOOD_DIR, "store": STORE_DIR},
            }
        })