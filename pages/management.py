from dash import html, dcc
import dash_bootstrap_components as dbc

layout = dbc.Container([
    html.H1("⚙️ 상태", className="text-center mb-4"),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🔧 상태 기능"),
                dbc.CardBody([
                    # 여기에 상태 관련 기능이 들어갈 예정
                ])
            ], className="shadow-sm")
        ])
    ])
], fluid=True, className="mt-4") 