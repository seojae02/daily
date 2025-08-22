"""
이 프로젝트는 기능별로 파일이 분리되어 있습니다.

실행은 아래와 같이 app.py를 통해 FastAPI 서버를 시작하세요:

    uvicorn app:app --host 0.0.0.0 --port 8000 --reload

주요 코드 분리:
    - config.py: 환경 변수 및 설정
    - utils.py: 공용 유틸 함수
    - routes_promo.py: 프로모션 텍스트 생성 라우트
    - routes_ad_image.py: 광고 이미지 생성 라우트
    - app.py: FastAPI 앱 및 라우트 등록

기존 main.py의 모든 기능은 위 파일들로 이동되었습니다.
"""
