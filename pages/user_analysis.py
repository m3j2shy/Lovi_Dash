from dash import html, dcc
import dash_bootstrap_components as dbc

def create_user_analysis_layout():
    return html.Div([
        html.H2("사용자 분석"),
        html.Div([
            html.Div([
                # 필터 요소들
                dbc.Row([
                    dbc.Col([
                        dcc.DatePickerRange(
                            id='user-date-picker',
                            start_date='2023-01-01',
                            end_date='2023-12-31'
                        )
                    ], width=6),
                    dbc.Col([
                        dcc.Dropdown(
                            id='user-segment-selector',
                            options=[
                                {'label': '신규 사용자', 'value': 'new'},
                                {'label': '재방문자', 'value': 'returning'},
                                {'label': '전체', 'value': 'all'}
                            ],
                            value='all'
                        )
                    ], width=6)
                ])
            ], className="filter-container"),
            
            html.Div([
                # 메인 차트
                dcc.Loading(
                    id="loading-user-behavior",
                    type="circle",
                    children=dcc.Graph(id='user-behavior-chart')
                )
            ], className="main-container"),
            
            html.Div([
                # 세부 정보
                dbc.Row([
                    dbc.Col([
                        html.H4("사용자 세션 길이"),
                        dcc.Loading(
                            id="loading-session-length",
                            type="circle",
                            children=dcc.Graph(id='session-length-chart')
                        )
                    ], width=6),
                    dbc.Col([
                        html.H4("페이지 체류 시간"),
                        dcc.Loading(
                            id="loading-page-duration",
                            type="circle",
                            children=dcc.Graph(id='page-duration-chart')
                        )
                    ], width=6)
                ])
            ], className="detail-container")
        ], className="page-container")
    ])

layout = create_user_analysis_layout() 