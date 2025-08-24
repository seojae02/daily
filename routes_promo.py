from fastapi import APIRouter, Form, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from typing import List, Optional, Tuple
import os
import re
import json
import requests

from config import GEMINI_API_KEY, GEMINI_ENDPOINT, MODEL_ID
from utils import (
    build_promo_prompt,
    filepaths_to_inline_parts,   # <-- 새로 추가된 util
    format_body_with_newlines_and_images,
)

router = APIRouter()

# 이미지가 저장된 로컬(서버) 디렉터리: 컨테이너 실행 시 -v로 마운트 권장
IMG_DIR = os.getenv("IMAGE_DIR", "/home/ec2-user/BE/img")


def _find_latest_index(img_dir: str) -> Optional[int]:
    """
    디렉터리 내에서 N_food_AI.jpg 패턴 중 가장 큰 N을 찾는다.
    없으면 None.
    """
    pat = re.compile(r"^(\d+)_food_AI\.jpg$", re.IGNORECASE)
    max_n = None
    try:
        for name in os.listdir(img_dir):
            m = pat.match(name)
            if m:
                n = int(m.group(1))
                if (max_n is None) or (n > max_n):
                    max_n = n
    except FileNotFoundError:
        return None
    return max_n


def _build_public_url(request: Request, filename: str) -> str:
    """
    nginx가 /images/ -> IMG_DIR alias로 서빙된다고 가정.
    프록시 환경 고려: X-Forwarded-* 헤더 우선 사용.
    """
    scheme = request.headers.get("X-Forwarded-Proto", request.url.scheme)
    host = request.headers.get("X-Forwarded-Host", request.headers.get("host", request.url.netloc))
    return f"{scheme}://{host}/images/{filename}"


@router.post("/v1/generate-promo")
def generate_promo(
    request: Request,
    debug: int = Query(0, description="1이면 모델 호출 없이 더미 반환"),
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
    업로드 이미지 없이도 동작.
    - IMG_DIR에서 가장 큰 N을 찾아 N_food_AI.jpg를 음식 이미지로 사용
    - 같은 번호의 N_food.jpg가 있으면 매장/참고 이미지로 추가 사용(옵셔널)
    - 이미지 URL은 /images/<파일명> 으로 생성해 본문에 균등 삽입
    """
    if debug == 1:
        demo_body = "디버그 응답입니다. 이미지 없이도 문장 줄바꿈/URL 삽입 포맷만 확인합니다!"
        demo_body = format_body_with_newlines_and_images(demo_body, [])
        return JSONResponse({
            "variants": [{
                "headline": f"{store_name} — {mood} 톤",
                "body": demo_body,
                "tags": ["#debug", "#fastapi"],
                "cta": "지금 바로 방문해 보세요",
            }]
        })

    # 1) 최신 N 찾기
    latest_n = _find_latest_index(IMG_DIR)
    food_ai_path = None
    store_img_path = None
    image_urls: List[str] = []

    if latest_n is not None:
        # 음식 이미지(필수 아님): N_food_AI.jpg
        candidate_food_ai = os.path.join(IMG_DIR, f"{latest_n}_food_AI.jpg")
        if os.path.exists(candidate_food_ai):
            food_ai_path = candidate_food_ai
            image_urls.append(_build_public_url(request, f"{latest_n}_food_AI.jpg"))

        # 매장/참고 이미지(옵셔널): N_food.jpg
        candidate_store = os.path.join(IMG_DIR, f"{latest_n}_food.jpg")
        if os.path.exists(candidate_store):
            store_img_path = candidate_store
            image_urls.append(_build_public_url(request, f"{latest_n}_food.jpg"))

    # 2) 프롬프트 생성
    prompt = build_promo_prompt(
        language=language, mood=mood, store_name=store_name,
        store_description=store_description, location_text=location_text,
        latitude=latitude, longitude=longitude, variants=variants,
    )

    # 3) Gemini 입력 parts 구성 (텍스트 + 최신 이미지들)
    parts: List[dict] = [{"text": prompt}]
    # 파일 경로를 base64 inlineData로 변환
    parts += filepaths_to_inline_parts([p for p in [store_img_path, food_ai_path] if p])

    # 4) LLM 호출
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

    # 코드펜스 제거
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:].strip()

    # 6) JSON 파싱 및 본문 포맷(문장 줄바꿈 + 이미지 URL 균등 삽입)
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

        # 이미지 경로/URL도 결과에 참고용으로 포함(디버깅/클라 편의를 위해)
        parsed["_images"] = {
            "food_ai": os.path.basename(food_ai_path) if food_ai_path else None,
            "store": os.path.basename(store_img_path) if store_img_path else None,
            "urls": image_urls,
            "used_index": latest_n,
        }

        return JSONResponse(parsed)
    except Exception:
        # 파싱 실패 시 raw 그대로 반환
        return JSONResponse({
            "raw": raw,
            "_images": {
                "food_ai": os.path.basename(food_ai_path) if food_ai_path else None,
                "store": os.path.basename(store_img_path) if store_img_path else None,
                "urls": image_urls,
                "used_index": latest_n,
            }
        })