from dash import html, dcc
import dash_bootstrap_components as dbc

def create_about_layout():
    return html.Div([
        html.H2([
            html.Img(src="assets/hamster.png", width="24", height="24", alt="Hamster", style={"margin": "0 5px"}),
            html.Img(src="assets/rabbit.png", width="24", height="24", alt="Rabbit", style={"margin": "0 5px"}),
            "LOVi 소개",
            html.Img(src="assets/t-rex.png", width="24", height="24", alt="T-Rex", style={"margin": "0 5px"}),
            html.Img(src="assets/spouting-whale.png", width="24", height="24", alt="Whale", style={"margin": "0 5px"})
        ], style={"display": "flex", "alignItems": "center", "justifyContent": "center"}),
        html.Div([
            html.Div([
                html.P("귀여운 웹 로그 대시보드 애플리케이션입니다."),
                html.Hr(),
                
                html.H4("🚀 배포 주소"),
                html.P([
                    html.A(
                        "https://lovi.my",
                        href="https://lovi.my",
                        target="_blank"
                    )
                ]),
                html.Hr(),
                
                html.H4("📋 프로젝트 개요"),
                html.Ul([
                    html.Li("Dash를 사용한 웹 로그 분석 대시보드"),
                    html.Li("Google BigQuery를 데이터 소스로 활용"),
                    html.Li("Cloud Run을 통한 서버리스 배포"),
                    html.Li("반응형 사이드바 네비게이션")
                ]),
                html.Hr(),
                
                html.H4("📊 데이터셋 출처"),
                html.P([
                    "이 프로젝트는 ",
                    html.A("Web Server Access Logs", href="https://www.kaggle.com/datasets/eliasdabbas/web-server-access-logs", target="_blank"),
                    " 데이터셋을 사용합니다."
                ]),
                html.Ul([
                    html.Li("출처: Kaggle"),
                    html.Li("제공자: Elias Dabbas"),
                    html.Li("라이센스: CC0: Public Domain")
                ]),
                html.Hr(),
                
                html.H4("🛠️ 기술 스택"),
                html.Ul([
                    html.Li("프레임워크: Dash (Python 기반 웹 애플리케이션 프레임워크)"),
                    html.Li("UI 컴포넌트: Dash Bootstrap Components"),
                    html.Li("데이터베이스: Google BigQuery"),
                    html.Li("배포: Google Cloud Run"),
                    html.Li("CI/CD: Google Cloud Build"),
                    html.Li("버전 관리: GitHub"),
                    html.Li("인프라: Docker, Google Cloud Platform")
                ]),
                html.Hr(),
                
                html.H4("📊 주요 기능"),
                html.Ul([
                    html.Li("실시간 트래픽 모니터링"),
                    html.Li("사용자 행동 분석"),
                    html.Li("인기 키워드 추적"),
                    html.Li("유입 경로 분석"),
                    html.Li("지역별 통계"),
                    html.Li("관리자 기능")
                ])
            ], className="about-content")
        ], className="page-container")
    ])

layout = create_about_layout() 