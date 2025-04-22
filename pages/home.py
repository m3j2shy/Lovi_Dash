from dash import html, dcc
import dash_bootstrap_components as dbc

def create_home_layout():
    return html.Div([
        html.H2("대시보드"),
        html.Div([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H4("실시간 트래픽"),
                        dcc.Loading(
                            id="loading-realtime-traffic",
                            type="circle",
                            children=dcc.Graph(id='realtime-traffic-chart')
                        )
                    ], className="chart-container")
                ], width=6),
                dbc.Col([
                    html.Div([
                        html.H4("사용자 행동"),
                        dcc.Loading(
                            id="loading-user-behavior",
                            type="circle",
                            children=dcc.Graph(id='user-behavior-chart')
                        )
                    ], className="chart-container")
                ], width=6)
            ], className="mb-4"),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H4("인기 키워드"),
                        dcc.Loading(
                            id="loading-popular-keywords",
                            type="circle",
                            children=dcc.Graph(id='popular-keywords-chart')
                        )
                    ], className="chart-container")
                ], width=6),
                dbc.Col([
                    html.Div([
                        html.H4("지역 분포"),
                        dcc.Loading(
                            id="loading-region-distribution",
                            type="circle",
                            children=dcc.Graph(id='region-distribution-chart')
                        )
                    ], className="chart-container")
                ], width=6)
            ])
        ], className="page-container")
    ])

layout = create_home_layout() 