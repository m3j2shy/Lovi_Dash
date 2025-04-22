from dash import html, dcc
import dash_bootstrap_components as dbc

def create_about_layout():
    return html.Div([
        html.H2("프로젝트 소개"),
        html.Div([
            html.Div([
                html.P("귀여운 웹 로그 대시보드 애플리케이션입니다."),
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
                    html.Li("CI/CD: GitHub Actions, Google Cloud Build"),
                    html.Li("버전 관리: GitHub"),
                    html.Li("인프라: Docker, Google Cloud Platform")
                ]),
                html.Hr(),
                html.H4("🚀 배포 주소"),
                html.P([
                    html.A(
                        "https://lovi-569292430057.asia-northeast3.run.app",
                        href="https://lovi-569292430057.asia-northeast3.run.app",
                        target="_blank"
                    )
                ])
            ], className="about-content")
        ], className="page-container")
    ])

layout = create_about_layout() 