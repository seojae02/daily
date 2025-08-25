# routes_upload_store.py
from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List
import os, re
from PIL import Image

router = APIRouter()

IMAGE_ROOT = os.getenv("IMAGE_DIR", "/home/ec2-user/BE/img")
FOOD_DIR   = os.path.join(IMAGE_ROOT, "food")
STORE_DIR  = os.path.join(IMAGE_ROOT, "store")

def _ensure_dir(p: str) -> None:
    os.makedirs(p, exist_ok=True)

def _scan_max_prefix(dir_path: str, pattern: str) -> int:
    """
    dir_path 내 파일명에서 정규식 pattern(그룹1=숫자)을 매칭해 최대 앞자리 숫자를 찾는다.
    """
    _ensure_dir(dir_path)
    pat = re.compile(pattern, re.IGNORECASE)
    max_n = 0
    for name in os.listdir(dir_path):
        m = pat.match(name)
        if m:
            try:
                max_n = max(max_n, int(m.group(1)))
            except ValueError:
                pass
    return max_n

def _next_group_index_across() -> int:
    """
    food/store 두 폴더 모두 검사해서 가장 큰 그룹번호 + 1
    - food 폴더는 ^(\d+)_food(_AI)?\.jpg
    - store 폴더는 ^(\d+)_store_\d+\.jpg
    """
    max_food  = _scan_max_prefix(FOOD_DIR,  r"^(\d+)_food(_AI)?\.jpg$")
    max_store = _scan_max_prefix(STORE_DIR, r"^(\d+)_store_\d+\.jpg$")
    return max(max_food, max_store) + 1

def _build_public_url(request: Request, subdir: str, filename: str) -> str:
    scheme = request.headers.get("X-Forwarded-Proto", request.url.scheme)
    host   = request.headers.get("X-Forwarded-Host", request.headers.get("host", request.url.netloc))
    # nginx: /images/ → /home/ec2-user/BE/img (subdir 포함)
    return f"{scheme}://{host}/images/{subdir}/{filename}"

@router.post("/v1/upload-store-images")
async def upload_store_images(
    request: Request,
    images: List[UploadFile] = File(..., description="가게 이미지들 (여러 개)"),
):
    if not images:
        raise HTTPException(status_code=400, detail="이미지가 없습니다.")

    _ensure_dir(STORE_DIR)
    n = _next_group_index_across()

    saved = []
    for i, uf in enumerate(images, start=1):
        try:
            img = Image.open(uf.file).convert("RGB")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"이미지 열기 실패: {e}")

        filename = f"{n}_store_{i}.jpg"
        path = os.path.join(STORE_DIR, filename)
        try:
            img.save(path, "JPEG", quality=95)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"이미지 저장 실패: {e}")

        saved.append({
            "filename": filename,
            "path": path,
            "url": _build_public_url(request, "store", filename),
        })

    return JSONResponse({
        "group": n,
        "count": len(saved),
        "files": saved,
        "note": "음식 가공본은 /v1/outpaint 호출 시 food/ 폴더에 N_food_AI.jpg 로 저장됩니다.",
    })
