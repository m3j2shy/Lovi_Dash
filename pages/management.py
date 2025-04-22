from dash import html, dcc
import dash_bootstrap_components as dbc

def create_management_layout():
    return html.Div([
        html.H2("관리"),
        html.Div([
            html.Div([
                # 필터 요소들
                dbc.Row([
                    dbc.Col([
                        dcc.DatePickerRange(
                            id='management-date-picker',
                            start_date='2023-01-01',
                            end_date='2023-12-31'
                        )
                    ], width=6),
                    dbc.Col([
                        dcc.Dropdown(
                            id='management-view-selector',
                            options=[
                                {'label': '시스템 상태', 'value': 'system'},
                                {'label': '사용자 관리', 'value': 'users'},
                                {'label': '데이터 관리', 'value': 'data'}
                            ],
                            value='system'
                        )
                    ], width=6)
                ])
            ], className="filter-container"),
            
            html.Div([
                # 메인 차트
                dcc.Loading(
                    id="loading-system-status",
                    type="circle",
                    children=dcc.Graph(id='system-status-chart')
                )
            ], className="main-container"),
            
            html.Div([
                # 세부 정보
                dbc.Row([
                    dbc.Col([
                        html.H4("리소스 사용량"),
                        dcc.Loading(
                            id="loading-resource-usage",
                            type="circle",
                            children=dcc.Graph(id='resource-usage-chart')
                        )
                    ], width=6),
                    dbc.Col([
                        html.H4("시스템 로그"),
                        dcc.Loading(
                            id="loading-system-logs",
                            type="circle",
                            children=dcc.Graph(id='system-logs-chart')
                        )
                    ], width=6)
                ])
            ], className="detail-container")
        ], className="page-container")
    ])

layout = create_management_layout() 