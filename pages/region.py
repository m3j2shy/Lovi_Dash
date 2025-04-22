from dash import html, dcc
import dash_bootstrap_components as dbc

def create_region_layout():
    return html.Div([
        html.H2("지역 분석"),
        html.Div([
            html.Div([
                # 필터 요소들
                dbc.Row([
                    dbc.Col([
                        dcc.DatePickerRange(
                            id='region-date-picker',
                            start_date='2023-01-01',
                            end_date='2023-12-31'
                        )
                    ], width=6),
                    dbc.Col([
                        dcc.Dropdown(
                            id='region-level-selector',
                            options=[
                                {'label': '국가', 'value': 'country'},
                                {'label': '지역', 'value': 'region'},
                                {'label': '도시', 'value': 'city'}
                            ],
                            value='country'
                        )
                    ], width=6)
                ])
            ], className="filter-container"),
            
            html.Div([
                # 메인 차트
                dcc.Loading(
                    id="loading-region-map",
                    type="circle",
                    children=dcc.Graph(id='region-map-chart')
                )
            ], className="main-container"),
            
            html.Div([
                # 세부 정보
                dbc.Row([
                    dbc.Col([
                        html.H4("상위 지역"),
                        dcc.Loading(
                            id="loading-top-regions",
                            type="circle",
                            children=dcc.Graph(id='top-regions-chart')
                        )
                    ], width=6),
                    dbc.Col([
                        html.H4("지역별 성장률"),
                        dcc.Loading(
                            id="loading-region-growth",
                            type="circle",
                            children=dcc.Graph(id='region-growth-chart')
                        )
                    ], width=6)
                ])
            ], className="detail-container")
        ], className="page-container")
    ])

layout = create_region_layout() 