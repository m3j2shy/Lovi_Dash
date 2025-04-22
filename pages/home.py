from dash import html, dcc
import dash_bootstrap_components as dbc

layout = dbc.Container([
    html.H1("홈", className="text-center mb-4"),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📊 트래픽 요약"),
                dbc.CardBody([
                    # 여기에 트래픽 관련 차트가 들어갈 예정
                ])
            ], className="mb-4 shadow-sm")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("👥 사용자 분석 요약"),
                dbc.CardBody([
                    # 여기에 사용자 분석 관련 차트가 들어갈 예정
                ])
            ], className="mb-4 shadow-sm")
        ], width=6)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔍 인기 키워드 요약"),
                dbc.CardBody([
                    # 여기에 인기 키워드 관련 차트가 들어갈 예정
                ])
            ], className="mb-4 shadow-sm")
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🛣️ 유입경로 요약"),
                dbc.CardBody([
                    # 여기에 유입경로 관련 차트가 들어갈 예정
                ])
            ], className="mb-4 shadow-sm")
        ], width=6)
    ])
], fluid=True, className="mt-4") 