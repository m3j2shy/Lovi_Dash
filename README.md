# 🐶🐹Lovi🐱🐰

귀여운 웹 로그 대시보드 애플리케이션입니다.

## 라이브러리 설치 방법

1. Python 3.13 설치

   - [Python 공식 웹사이트](https://www.python.org/downloads/)에서 Python 3.13 설치

2. 가상환경 생성 및 활성화

   ```bash
   # 가상환경 생성
   python -m venv .venv

   # Windows에서 가상환경 활성화
   .\.venv\Scripts\activate

   # macOS/Linux에서 가상환경 활성화
   source .venv/bin/activate
   ```

3. 필요한 라이브러리 설치
   ```bash
   # requirements.txt에 있는 라이브러리 설치
   pip install -r requirements.txt
   ```

## GCP Cloud Run 배포 방법

1. Google Cloud SDK 설치
2. 프로젝트 설정

```bash
gcloud config set project YOUR_PROJECT_ID
```

3. 이미지 빌드 및 푸시

```bash
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/olympic-dashboard
```

4. Cloud Run 서비스 배포

```bash
gcloud run deploy olympic-dashboard --image gcr.io/YOUR_PROJECT_ID/olympic-dashboard --platform managed --region asia-northeast3 --allow-unauthenticated
```
