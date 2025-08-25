from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List
import os
import re
from PIL import Image

router = APIRouter()

IMG_DIR = os.getenv("IMAGE_DIR", "/home/ec2-user/BE/img")

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _next_group_index(save_dir: str) -> int:
    """
    save_dir 안의 파일들 중 맨 앞 숫자 N을 추출해서 가장 큰 N+1 반환.
    예: 3_food.jpg, 3_store_1.jpg, 10_food_AI.jpg -> 다음은 11
    """
    max_n = 0
    try:
        for name in os.listdir(save_dir):
            m = re.match(r"^(\d+)_", name)
            if m:
                n = int(m.group(1))
                if n > max_n:
                    max_n = n
    except FileNotFoundError:
        pass
    return max_n + 1

def _build_public_url(request: Request, filename: str) -> str:
    scheme = request.headers.get("X-Forwarded-Proto", request.url.scheme)
    host = request.headers.get("X-Forwarded-Host", request.headers.get("host", request.url.netloc))
    return f"{scheme}://{host}/images/{filename}"

@router.post("/v1/upload-store-images")
async def upload_store_images(
    request: Request,
    images: List[UploadFile] = File(..., description="가게 이미지들 (여러 개 업로드 가능)"),
):
    """
    저장 규칙:
    - 그룹 번호 N = 폴더 내 가장 큰 번호 + 1
    - 파일명: N_store_1.jpg, N_store_2.jpg, ...
    """
    if not images:
        raise HTTPException(status_code=400, detail="이미지가 없습니다.")

    _ensure_dir(IMG_DIR)
    n = _next_group_index(IMG_DIR)

    saved_files = []
    for i, uf in enumerate(images, start=1):
        try:
            img = Image.open(uf.file).convert("RGB")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"이미지 열기 실패: {e}")

        filename = f"{n}_store_{i}.jpg"
        path = os.path.join(IMG_DIR, filename)
        try:
            img.save(path, "JPEG", quality=95)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"이미지 저장 실패: {e}")

        saved_files.append({
            "filename": filename,
            "path": path,
            "url": _build_public_url(request, filename),
        })

    return JSONResponse({
        "group": n,
        "count": len(saved_files),
        "files": saved_files,
        "note": "가공된 음식 이미지는 /v1/outpaint 호출로 생성되며 N_food_AI.jpg 로 저장됩니다.",
    })