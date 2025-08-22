import os
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
_raw_model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
MODEL_ID = _raw_model.split("/")[-1]
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_ID}:generateContent"

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY가 없습니다. 프로젝트 루트의 .env를 확인하세요.")
