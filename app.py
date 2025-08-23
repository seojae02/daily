from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes_promo import router as promo_router
from routes_ad_image import router as ad_image_router

app = FastAPI(
    title="Promo & Ad Image Generator (FastAPI)",
    version="1.0.0",
    description="Gemini REST/SDK + SD Inpaint + rembg 조합 백엔드",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

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
            "/v1/ad-image (POST form-data; return=image|json)",
        ],
        "docs": "/docs",
    }

app.include_router(promo_router)
# app.include_router(ad_image_router)
