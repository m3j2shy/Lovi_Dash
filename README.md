# <img src="assets/hamster.png" width="24" height="24" alt="Hamster"> <img src="assets/rabbit.png" width="24" height="24" alt="Rabbit"> Lovi <img src="assets/t-rex.png" width="24" height="24" alt="T-Rex"> <img src="assets/spouting-whale.png" width="24" height="24" alt="Whale">

<p align="center">
  <img src="assets/lovi-logo.gif" height="100" alt="Lovi Logo">
</p>

귀여운 웹 로그 대시보드 애플리케이션입니다.

## 🚀 배포 주소

https://lovi.my

## 📋 프로젝트 개요

- Dash를 사용한 웹 로그 분석 대시보드
- Google BigQuery를 데이터 소스로 활용
- Cloud Run을 통한 서버리스 배포
- 반응형 사이드바 네비게이션

## 📊 데이터셋 출처

이 프로젝트는 [Web Server Access Logs](https://www.kaggle.com/datasets/eliasdabbas/web-server-access-logs) 데이터셋을 사용합니다.

- 출처: Kaggle
- 제공자: Elias Dabbas
- 라이센스: CC0: Public Domain

## 🛠️ 기술 스택

- **프레임워크**: Dash (Python 기반 웹 애플리케이션 프레임워크)
- **UI 컴포넌트**: Dash Bootstrap Components
- **데이터베이스**: Google BigQuery
- **배포**: Google Cloud Run
- **CI/CD**: Google Cloud Build
- **버전 관리**: GitHub
- **인프라**: Docker, Google Cloud Platform

## 🚀 시작하기

### 필수 요구사항

- Python 3.13
- Google Cloud Platform 계정
- BigQuery 접근 권한

### 개발 환경 설정

1. **Python 3.13 설치**

   - [Python 공식 웹사이트](https://www.python.org/downloads/)에서 Python 3.13 설치

2. **가상환경 생성 및 활성화**

   ```bash
   # 가상환경 생성
   python -m venv .venv

   # Windows에서 가상환경 활성화
   .\.venv\Scripts\activate

   # macOS/Linux에서 가상환경 활성화
   source .venv/bin/activate
   ```

3. **의존성 설치**

   ```bash
   pip install -r requirements.txt
   ```

4. **환경 변수 설정**
   - `.env` 파일 생성
   ```bash
   GCP_PROJECT_ID=your-project-id
   BIGQUERY_DATASET=your-dataset
   BIGQUERY_TABLE=your-table
   ```

### 로컬 실행

```bash
python app.py
```

## 📊 기능

- 실시간 트래픽 모니터링
- 사용자 행동 분석
- 인기 키워드 추적
- 유입 경로 분석
- 지역별 통계
- 관리자 기능
