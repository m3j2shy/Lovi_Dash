from dash import html, dcc
import dash_bootstrap_components as dbc

def create_referrer_layout():
    return html.Div([
        html.H2("유입 출처"),
        html.Div([
            html.Div([
                # 필터 요소들
                dbc.Row([
                    dbc.Col([
                        dcc.DatePickerRange(
                            id='referrer-date-picker',
                            start_date='2023-01-01',
                            end_date='2023-12-31'
                        )
                    ], width=6),
                    dbc.Col([
                        dcc.Dropdown(
                            id='referrer-type-selector',
                            options=[
                                {'label': '전체', 'value': 'all'},
                                {'label': '검색 엔진', 'value': 'search'},
                                {'label': '소셜 미디어', 'value': 'social'},
                                {'label': '직접 방문', 'value': 'direct'}
                            ],
                            value='all'
                        )
                    ], width=6)
                ])
            ], className="filter-container"),
            
            html.Div([
                # 메인 차트
                dcc.Loading(
                    id="loading-referrer-sankey",
                    type="circle",
                    children=dcc.Graph(id='referrer-sankey-chart')
                )
            ], className="main-container"),
            
            html.Div([
                # 세부 정보
                dbc.Row([
                    dbc.Col([
                        html.H4("상위 유입 출처"),
                        dcc.Loading(
                            id="loading-top-referrer",
                            type="circle",
                            children=dcc.Graph(id='top-referrer-chart')
                        )
                    ], width=6),
                    dbc.Col([
                        html.H4("유입 출처별 전환율"),
                        dcc.Loading(
                            id="loading-conversion-rate",
                            type="circle",
                            children=dcc.Graph(id='conversion-rate-chart')
                        )
                    ], width=6)
                ])
            ], className="detail-container")
        ], className="page-container")
    ])

layout = create_referrer_layout() 