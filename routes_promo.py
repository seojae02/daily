from fastapi import APIRouter, Form, File, UploadFile, Query, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
import requests
import json
from config import GEMINI_API_KEY, GEMINI_ENDPOINT, MODEL_ID
from utils import build_promo_prompt, files_to_inline_parts
from utils import build_promo_prompt, files_to_inline_parts, format_body_with_newlines_and_images

router = APIRouter()

@router.post("/v1/generate-promo")
def generate_promo(
    debug: int = Query(0, description="1이면 모델 호출 없이 더미 반환"),
    store_name: str = Form(...),
    mood: str = Form(...),
    store_description: Optional[str] = Form(None),
    location_text: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    variants: int = Form(3),
    language: str = Form("ko"),
    store_images: Optional[List[UploadFile]] = File(None),
    food_images: Optional[List[UploadFile]] = File(None),
    image_urls: Optional[List[str]] = Form(None),
):
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

    prompt = build_promo_prompt(
        language=language, mood=mood, store_name=store_name,
        store_description=store_description, location_text=location_text,
        latitude=latitude, longitude=longitude, variants=variants,
    )
    parts: List[dict] = [{"text": prompt}]
    parts += files_to_inline_parts(store_images)
    parts += files_to_inline_parts(food_images)

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
    try:
        parsed = json.loads(raw)
        if not isinstance(parsed, dict) or "variants" not in parsed:
            raise ValueError("variants 키 없음")

        # 🔧 본문 포맷팅: 문장별 줄바꿈 + 이미지 URL 균등 삽입
        if isinstance(parsed.get("variants"), list):
            for v in parsed["variants"]:
                if isinstance(v, dict) and "body" in v:
                    v["body"] = format_body_with_newlines_and_images(
                        v.get("body", ""), image_urls
                    )

        return JSONResponse(parsed)
    except Exception:
        return JSONResponse({"raw": raw})

