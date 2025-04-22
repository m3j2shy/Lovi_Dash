from dash import html, dcc
import dash_bootstrap_components as dbc

layout = dbc.Container([
    html.H1("🔍 인기 키워드", className="text-center mb-4"),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📈 키워드 통계"),
                dbc.CardBody([
                    # 여기에 인기 키워드 관련 차트가 들어갈 예정
                ])
            ], className="shadow-sm")
        ])
    ])
], fluid=True, className="mt-4") 