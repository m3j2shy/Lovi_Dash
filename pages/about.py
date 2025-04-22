from dash import html, dcc
import dash_bootstrap_components as dbc

layout = dbc.Container([
    html.H1("ℹ️ 프로젝트 소개", className="text-center mb-4"),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🐶🐹Lovi🐱🐰 Dashboard"),
                dbc.CardBody([
                    html.P("Lovi Dashboard는 반려동물 관련 데이터를 분석하고 시각화하는 대시보드입니다."),
                    html.P("주요 기능:"),
                    html.Ul([
                        html.Li("📊 트래픽 분석"),
                        html.Li("👥 사용자 행동 분석"),
                        html.Li("🔍 인기 키워드 분석"),
                        html.Li("🛣️ 유입경로 분석"),
                        html.Li("🌍 지역별 분석"),
                    ])
                ])
            ], className="shadow-sm")
        ])
    ])
], fluid=True, className="mt-4") 