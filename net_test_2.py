import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# API 키는 헤더가 아니라 URL 파라미터로!
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"

headers = {"Content-Type": "application/json"}
data = {
    "contents": [
        {"parts": [{"text": "한 줄 소개: 따뜻한 분위기의 파스타집 홍보문구 한 문장."}]}
    ]
}

resp = requests.post(url, headers=headers, json=data, timeout=20)
print("status:", resp.status_code)
print("body:", resp.text[:500])