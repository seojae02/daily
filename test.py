# import os, time
# from dotenv import load_dotenv
# import google.generativeai as genai
#
# def main():
#     load_dotenv()
#     api = os.getenv("GEMINI_API_KEY")
#     print("ENV key loaded? ->", bool(api))
#     if not api:
#         print("❌ .env에서 GEMINI_API_KEY를 못 읽었습니다.")
#         return
#
#     genai.configure(api_key=api)
#
#     try:
#         model = genai.GenerativeModel("models/gemini-1.5-flash")
#         t0 = time.time()
#         resp = model.generate_content(
#             "한 줄 소개: 따뜻한 분위기의 파스타집 홍보문구 한 문장.",
#             request_options={"timeout": 10},
#         )
#         took = time.time() - t0
#         ok = bool(getattr(resp, "text", ""))
#         print("OK?", ok, "elapsed=", round(took, 2), "s")
#         print((resp.text or "")[:200])
#     except Exception as e:
#         import traceback, sys
#         print("❌ generate_content 실패:", repr(e))
#         traceback.print_exc(file=sys.stdout)
#
# if __name__ == "__main__":
#     main()