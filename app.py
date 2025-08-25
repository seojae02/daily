from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes_promo import router as promo_router
from openai_seojae import router as outpaint_router
from routes_upload_store import router as upload_store_router  # ✅ 신규 업로드 라우터

app = FastAPI(
    title="Promo & Ad Image Generator (FastAPI)",
    version="1.0.0",
    description="Gemini REST/SDK + SD Inpaint + rembg 조합 백엔드",
)

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
#     allow_credentials=True,
# )

@app.get("/health")
def health():
    from config import MODEL_ID
    import torch
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    return {"ok": True, "model": MODEL_ID, "device": DEVICE}

@app.get("/")
def index():
    return {
        "message": "Promo & Ad Image backend is running.",
        "endpoints": [
            "/health",
            "/v1/generate-promo (POST form-data)",
            "/v1/upload-store-images (POST form-data, multiple files)",
            "/v1/outpaint (POST form-data)",
        ],
        "docs": "/docs",
    }

app.include_router(promo_router)
app.include_router(outpaint_router)
app.include_router(upload_store_router)  # ✅ 추가