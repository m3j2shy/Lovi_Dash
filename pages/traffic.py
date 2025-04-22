from dash import html, dcc
import dash_bootstrap_components as dbc

def create_traffic_layout():
    return html.Div([
        html.H2("트래픽 분석"),
        html.Div([
            html.Div([
                # 필터 요소들
                dbc.Row([
                    dbc.Col([
                        dcc.DatePickerRange(
                            id='traffic-date-picker',
                            start_date='2023-01-01',
                            end_date='2023-12-31'
                        )
                    ], width=6),
                    dbc.Col([
                        dcc.Dropdown(
                            id='traffic-metric-selector',
                            options=[
                                {'label': '방문자 수', 'value': 'visitors'},
                                {'label': '페이지뷰', 'value': 'pageviews'},
                                {'label': '세션 수', 'value': 'sessions'}
                            ],
                            value='visitors'
                        )
                    ], width=6)
                ])
            ], className="filter-container"),
            
            html.Div([
                # 메인 차트
                dcc.Loading(
                    id="loading-traffic-trend",
                    type="circle",
                    children=dcc.Graph(id='traffic-trend-chart')
                )
            ], className="main-container"),
            
            html.Div([
                # 세부 정보
                dbc.Row([
                    dbc.Col([
                        html.H4("시간대별 트래픽"),
                        dcc.Loading(
                            id="loading-hourly-traffic",
                            type="circle",
                            children=dcc.Graph(id='hourly-traffic-chart')
                        )
                    ], width=6),
                    dbc.Col([
                        html.H4("요일별 트래픽"),
                        dcc.Loading(
                            id="loading-daily-traffic",
                            type="circle",
                            children=dcc.Graph(id='daily-traffic-chart')
                        )
                    ], width=6)
                ])
            ], className="detail-container")
        ], className="page-container")
    ])

layout = create_traffic_layout() 