from dash import html, dcc
import dash_bootstrap_components as dbc

layout = dbc.Container([
    html.H1("🛣️ 유입경로 분석", className="text-center mb-4"),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📊 유입경로 통계"),
                dbc.CardBody([
                    # 여기에 유입경로 관련 차트가 들어갈 예정
                ])
            ], className="shadow-sm")
        ])
    ])
], fluid=True, className="mt-4") 