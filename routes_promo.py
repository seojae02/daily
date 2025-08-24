from fastapi import APIRouter, Form, Query, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Optional, List
import requests
import json
import os

from config import GEMINI_API_KEY, GEMINI_ENDPOINT
from utils import (
    build_promo_prompt,
    format_body_with_newlines_and_images,
    image_file_to_inline_part,
)

router = APIRouter()

IMG_DIR = "/home/ec2-user/BE/img"  # 서버 로컬 이미지 저장 경로

@router.post("/v1/generate-promo")
def generate_promo(
    request: Request,
    identifier: str = Form(..., description="이미지 식별자 (ex: abc123)"),
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
    - 클라이언트가 image_urls를 주지 않아도 됨.
    - 서버 경로의 {identifier}_food_AI.jpg가 존재하면 이를 퍼블릭 URL로 만들어 본문에 균등 삽입.
    - Gemini 입력용 이미지도 서버 파일(음식/가게)을 inlineData로 선택적으로 첨부.
    """

    # --------------------------
    # 0) 디버그 모드
    # --------------------------
    # 본문에 서버 이미지 URL 자동 삽입 (있는 경우)
    base_url = str(request.base_url).rstrip("/")  # 예: http://<host>:8000
    food_filename = f"{identifier}_food_AI.jpg"
    food_path = os.path.join(IMG_DIR, food_filename)

    image_urls: List[str] = []
    if os.path.exists(food_path):
        # app.py에서 StaticFiles로 /images -> /home/ec2-user/BE/img 마운트되어 있어야 함
        image_urls.append(f"{base_url}/images/{food_filename}")

    if debug == 1:
        demo_body = (
            "디버그 응답입니다. 엔드포인트 연결만 점검합니다. "
            "줄바꿈과 이미지 URL 삽입 테스트 문장입니다!"
        )
        demo_body = format_body_with_newlines_and_images(demo_body, image_urls)
        return JSONResponse({
            "variants": [{
                "headline": f"{store_name} — {mood} 톤",
                "body": demo_body,
                "tags": ["#debug", "#fastapi"],
                "cta": "지금 바로 방문해 보세요",
            }]
        })

    # --------------------------
    # 1) 프롬프트 생성
    # --------------------------
    prompt = build_promo_prompt(
        language=language,
        mood=mood,
        store_name=store_name,
        store_description=store_description,
        location_text=location_text,
        latitude=latitude,
        longitude=longitude,
        variants=variants,
    )
    parts = [{"text": prompt}]

    # --------------------------
    # 2) Gemini 입력용 이미지 (선택)
    #    - 음식 이미지: {identifier}_food_AI.jpg (있으면 첨부)
    #    - 가게 이미지: {identifier}_store.jpg (있으면 첨부)
    # --------------------------
    store_filename = f"{identifier}_store.jpg"
    store_path = os.path.join(IMG_DIR, store_filename)

    food_part = image_file_to_inline_part(food_path)
    store_part = image_file_to_inline_part(store_path)

    if food_part:
        parts.append(food_part)
    if store_part:
        parts.append(store_part)

    # --------------------------
    # 3) Gemini API 호출
    # --------------------------
    url = f"{GEMINI_ENDPOINT}?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": parts}]}

    try:
        r = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=90
        )
        r.raise_for_status()
        resp_json = r.json()
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="LLM 호출 타임아웃(90s)")
    except requests.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"LLM HTTP 오류: {e.response.status_code} {e.response.text[:300]}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 호출 실패: {repr(e)}")

    # --------------------------
    # 4) 응답 파싱
    # --------------------------
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

    # JSON으로 파싱 & 본문에 이미지 URL 균등 삽입
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

        return JSONResponse(parsed)
    except Exception:
        # 모델이 JSON 스키마를 지키지 못했을 때 raw 반환
        return JSONResponse({"raw": raw})