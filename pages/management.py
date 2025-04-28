from dash import html, dcc, callback, Output, Input, State, ctx, dash_table
import dash_bootstrap_components as dbc
from utils.utils import load_bigquery_data
import pandas as pd
import datetime
import plotly.graph_objects as go
import math

# 공통 상수 정의
ORDERED_STATUS_CODES = ['1xx', '2xx', '3xx', '4xx', '5xx']
COLOR_MAP = {
    '1xx': '#9C27B0',  # 정보 응답 - 보라색
    '2xx': '#66BB6A',  # 성공 - 녹색
    '3xx': '#42A5F5',  # 리다이렉션 - 파란색
    '4xx': '#FFA726',  # 클라이언트 오류 - 주황색
    '5xx': '#EF5350'   # 서버 오류 - 빨간색
}

# 날짜 데이터 조회
query_result = load_bigquery_data("""
SELECT DISTINCT
  DATE(timestamp_utc) as date
FROM
  `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
ORDER BY
  date
""")

# 날짜 범위 계산
min_date_str = '2019-01-01'  # 기본값
max_date_str = datetime.date.today().strftime('%Y-%m-%d')  # 기본값

if not query_result.empty:
    query_result['date'] = pd.to_datetime(query_result['date']).dt.date
    min_date = query_result['date'].min()
    max_date = query_result['date'].max()
    min_date_str = min_date.strftime('%Y-%m-%d')
    max_date_str = max_date.strftime('%Y-%m-%d')

# HTTP 상태 코드 그룹 정의
status_code_groups = [
    {'label': '1xx', 'value': '1xx', 'title': '정보 응답'},
    {'label': '2xx', 'value': '2xx', 'title': '성공'},
    {'label': '3xx', 'value': '3xx', 'title': '리다이렉션'},
    {'label': '4xx', 'value': '4xx', 'title': '클라이언트 오류'},
    {'label': '5xx', 'value': '5xx', 'title': '서버 오류'}
]

# 초기 상태 코드 데이터 조회
initial_status_query = f"""
SELECT 
    FLOOR(status_code/100)*100 AS status_group,
    COUNT(*) as count
FROM 
    `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
WHERE 
    DATE(timestamp_utc) BETWEEN '{min_date_str}' AND '{max_date_str}'
GROUP BY 
    status_group
ORDER BY 
    status_group
"""
initial_status_df = load_bigquery_data(initial_status_query)
if not initial_status_df.empty:
    initial_status_groups = [int(x) for x in initial_status_df['status_group'].tolist()]
else:
    initial_status_groups = []

def create_error_ip_table(error_type):
    """오류 IP 테이블 컴포넌트를 생성합니다."""
    return html.Div([
        html.H4(f"{error_type} 에러 발생 상위 10개 IP", style={"marginBottom": "10px"}),
        dcc.Loading(
            id=f"loading-{error_type}-ips",
            type="circle",
            children=dash_table.DataTable(
                id=f"{error_type}-ips-table",
                columns=[
                    {"name": "순위", "id": "rank"},
                    {"name": "IP 주소", "id": "ip"},
                    {"name": "요청 수", "id": "count"},
                    {"name": "국가/지역", "id": "geo"}
                ],
                style_table={"overflowX": "auto"},
                style_cell={
                    "textAlign": "left",
                    "padding": "8px",
                    "fontFamily": "Arial, sans-serif"
                },
                style_header={
                    "backgroundColor": "#f8f9fa",
                    "fontWeight": "bold",
                    "textAlign": "center"
                },
                style_data_conditional=[
                    {
                        "if": {"row_index": "odd"},
                        "backgroundColor": "#f8f9fa"
                    }
                ],
                page_size=10
            )
        )
    ])

def create_error_search_section():
    """로그 상세 검색 섹션을 생성합니다."""
    return html.Div([
        # 검색 필터
        html.Div([
            # 날짜 및 시간 범위
            html.Label("조회 기간", style={"marginBottom": "5px"}),
            html.Div([
                # 시작 날짜/시간
                html.Div([
                    html.Label("시작", style={"fontSize": "0.9rem", "marginBottom": "5px"}),
                    html.Div([
                        html.Div([
                            dcc.DatePickerSingle(
                                id='log-search-start-date',
                                date=min_date_str,
                                display_format='YYYY-MM-DD',
                                style={"width": "130px"}
                            )
                        ], style={
                            "marginRight": "10px",
                            "display": "inline-block"
                        }),
                        dbc.Input(
                            id='log-search-start-time',
                            type='time',
                            value='00:00',
                            style={
                                "height": "46px",
                                "padding": "6px 12px",
                                "fontSize": "1rem"
                            }
                        )
                    ], style={"display": "flex", "alignItems": "center"})
                ], style={"marginRight": "30px"}),
                # 종료 날짜/시간
                html.Div([
                    html.Label("종료", style={"fontSize": "0.9rem", "marginBottom": "5px"}),
                    html.Div([
                        html.Div([
                            dcc.DatePickerSingle(
                                id='log-search-end-date',
                                date=max_date_str,
                                display_format='YYYY-MM-DD',
                                style={"width": "130px"}
                            )
                        ], style={
                            "marginRight": "10px",
                            "display": "inline-block"
                        }),
                        dbc.Input(
                            id='log-search-end-time',
                            type='time',
                            value='23:59',
                            style={
                                "height": "46px",
                                "padding": "6px 12px",
                                "fontSize": "1rem"
                            }
                        )
                    ], style={"display": "flex", "alignItems": "center"})
                ])
            ], style={"display": "flex", "marginBottom": "15px"}),
            
            # 검색 필드들
            dbc.Row([
                # IP 주소 검색
                dbc.Col([
                    html.Label("IP 주소", style={"fontSize": "0.9rem", "marginBottom": "5px"}),
                    dbc.Input(
                        id='log-search-ip',
                        type='text',
                        placeholder='예: 192.168.1.1',
                        style={"marginBottom": "10px"}
                    )
                ], width=3),
                # URL 검색
                dbc.Col([
                    html.Label("URL", style={"fontSize": "0.9rem", "marginBottom": "5px"}),
                    dbc.Input(
                        id='log-search-url',
                        type='text',
                        placeholder='예: /api/users',
                        style={"marginBottom": "10px"}
                    )
                ], width=3),
                # 국가/지역 검색
                dbc.Col([
                    html.Label("국가/지역", style={"fontSize": "0.9rem", "marginBottom": "5px"}),
                    dbc.Input(
                        id='log-search-geo',
                        type='text',
                        placeholder='예: Korea',
                        style={"marginBottom": "10px"}
                    )
                ], width=3),
                # User Agent 검색
                dbc.Col([
                    html.Label("User Agent", style={"fontSize": "0.9rem", "marginBottom": "5px"}),
                    dbc.Input(
                        id='log-search-user-agent',
                        type='text',
                        placeholder='예: Chrome, Bot',
                        style={"marginBottom": "10px"}
                    )
                ], width=3)
            ]),
            
            dbc.Button(
                "검색",
                id='log-search-button',
                color="primary",
                className="me-2"
            )
        ], style={
            "padding": "20px",
            "backgroundColor": "#f8f9fa",
            "borderRadius": "8px",
            "border": "1px solid #e9ecef",
            "marginBottom": "20px"
        }),
        # 검색 결과 테이블
        html.Div([
            html.H4("검색 결과", style={"marginBottom": "10px"}),
            dcc.Loading(
                id="loading-log-search",
                type="circle",
                children=[
                    html.Div(
                        id="log-search-info",
                        style={
                            "marginBottom": "10px",
                            "fontSize": "0.9rem",
                            "color": "#666",
                            "textAlign": "right"
                        }
                    ),
                    dash_table.DataTable(
                        id="log-search-table",
                        columns=[
                            {"name": "IP 주소", "id": "ip"},
                            {"name": "상태 코드", "id": "status_code"},
                            {"name": "요청 시간", "id": "timestamp"},
                            {"name": "요청 URL", "id": "url"},
                            {"name": "국가/지역", "id": "geo"},
                            {"name": "HTTP 메서드", "id": "http_method"},
                            {"name": "브라우저", "id": "user_browser"},
                            {"name": "OS", "id": "user_os"},
                            {"name": "모바일", "id": "user_is_mobile"},
                            {"name": "봇", "id": "user_is_bot"}
                        ],
                        style_table={"overflowX": "auto"},
                        style_cell={
                            "textAlign": "left",
                            "padding": "8px",
                            "fontFamily": "Arial, sans-serif",
                            "maxWidth": "200px",
                            "whiteSpace": "normal",
                            "textOverflow": "ellipsis"
                        },
                        style_header={
                            "backgroundColor": "#f8f9fa",
                            "fontWeight": "bold",
                            "textAlign": "center"
                        },
                        style_data_conditional=[
                            {
                                "if": {"row_index": "odd"},
                                "backgroundColor": "#f8f9fa"
                            }
                        ],
                        page_size=10,
                        page_current=0,
                        page_action="custom",
                        sort_action="custom",
                        sort_mode="single",
                        filter_action="none",
                        css=[{
                            'selector': '.dash-spreadsheet-container .dash-spreadsheet-inner td',
                            'rule': 'font-family: Arial, sans-serif;'
                        }, {
                            'selector': '.dash-spreadsheet-container .dash-spreadsheet-inner .dash-spreadsheet-pagination',
                            'rule': 'text-align: right;'
                        }]
                    )
                ]
            )
        ])
    ])

def create_status_code_cards():
    """상태 코드 통계 카드를 생성합니다."""
    return html.Div([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3("2xx Status Codes", className="card-title text-success"),
                        html.H2(
                            id="2xx-count",
                            className="card-text text-success",
                            style={"fontSize": "3rem", "fontWeight": "bold"}
                        )
                    ])
                ], className="mb-4 text-center")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3("3xx Status Codes", className="card-title text-primary"),
                        html.H2(
                            id="3xx-count",
                            className="card-text text-primary",
                            style={"fontSize": "3rem", "fontWeight": "bold"}
                        )
                    ])
                ], className="mb-4 text-center")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3("4xx Status Codes", className="card-title text-warning"),
                        html.H2(
                            id="4xx-count",
                            className="card-text text-warning",
                            style={"fontSize": "3rem", "fontWeight": "bold"}
                        )
                    ])
                ], className="mb-4 text-center")
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H3("5xx Status Codes", className="card-title text-danger"),
                        html.H2(
                            id="5xx-count",
                            className="card-text text-danger",
                            style={"fontSize": "3rem", "fontWeight": "bold"}
                        )
                    ])
                ], className="mb-4 text-center")
            ], width=3)
        ])
    ])

def create_management_layout():
    """관리 페이지 레이아웃을 생성합니다."""
    return html.Div([
        html.H2("상태 코드 분석", style={"textAlign": "center"}),
        html.Div([
            # 필터 섹션
            html.Div([
                # 날짜 선택기
                html.Div([
                    html.Label("날짜 범위", className="filter-label"),
                    html.Div([
                        html.Div([
                            html.Label("시작 날짜:", style={"marginRight": "10px", "fontWeight": "normal", "fontSize": "0.9rem"}),
                            dcc.DatePickerSingle(
                                id='management-start-date',
                                date=min_date_str,
                                display_format='YYYY-MM-DD'
                            )
                        ], style={"display": "inline-block", "marginRight": "15px"}),
                        html.Div([
                            html.Label("종료 날짜:", style={"marginRight": "10px", "fontWeight": "normal", "fontSize": "0.9rem"}),
                            dcc.DatePickerSingle(
                                id='management-end-date',
                                date=max_date_str,
                                display_format='YYYY-MM-DD'
                            )
                        ], style={"display": "inline-block"})
                    ], style={"display": "flex", "alignItems": "center", "marginTop": "5px"})
                ])
            ], className="filter-container"),
            
            # 메인 차트 섹션
            html.Div([
                # 상태 코드 카드 섹션
                create_status_code_cards(),
                
                dbc.Row([
                    # 상태 코드 분포 차트
                    dbc.Col([
                        html.Div([
                            html.H4("상태 코드 분포", style={"marginBottom": "5px"}),
                            dbc.ButtonGroup([
                                dbc.Button("로그 스케일", id="pie-log", color="primary", outline=True, size="sm", className="me-1", active=True),
                                dbc.Button("일반", id="pie-normal", color="primary", outline=True, size="sm")
                            ], size="sm", style={"marginBottom": "5px"})
                        ], style={"marginBottom": "10px"}),
                        dcc.Loading(
                            id="loading-status-distribution",
                            type="circle",
                            children=dcc.Graph(id='status-distribution-chart')
                        ),
                        dcc.Store(id='pie-chart-mode', data='log')
                    ], width=6),
                    # 시간별 상태 코드 차트
                    dbc.Col([
                        html.Div([
                            html.H4("시간별 상태 코드", style={"marginBottom": "5px"}),
                            dbc.ButtonGroup([
                                dbc.Button("로그 스케일", id="scale-log", color="primary", outline=True, size="sm", className="me-1", active=True),
                                dbc.Button("일반", id="scale-normal", color="primary", outline=True, size="sm", className="me-1"),
                                dbc.Button("백분율 (%)", id="scale-normalize", color="primary", outline=True, size="sm")
                            ], size="sm", style={"marginBottom": "5px"})
                        ], style={"marginBottom": "10px"}),
                        dcc.Loading(
                            id="loading-hourly-status",
                            type="circle",
                            children=dcc.Graph(id='hourly-status-chart')
                        ),
                        dcc.Store(id='hourly-chart-mode', data='log')
                    ], width=6)
                ])
            ], className="main-container"),
            
            # 세부 정보 섹션
            html.Div([
                html.H3("로그 상세 검색", style={"marginBottom": "20px"}),
                create_error_search_section(),
                html.Hr(style={"margin": "30px 0 20px 0"}),
                html.H3("오류 발생 IP 분석", style={"marginBottom": "20px"}),
                dbc.Row([
                    dbc.Col([create_error_ip_table("4xx")], width=6),
                    dbc.Col([create_error_ip_table("5xx")], width=6)
                ])
            ], className="detail-container")
        ], className="page-container")
    ])

@callback(
    Output('status-codes-store', 'children'),
    [Input('management-start-date', 'date'),
     Input('management-end-date', 'date')]
)
def query_status_codes(start_date, end_date):
    if not start_date or not end_date:
        return str(initial_status_groups)
    
    query = f"""
    SELECT 
        FLOOR(status_code/100)*100 AS status_group,
        COUNT(*) as count
    FROM 
        `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
    WHERE 
        DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY 
        status_group
    ORDER BY 
        status_group
    """
    
    status_df = load_bigquery_data(query)
    
    if not status_df.empty:
        status_groups = [int(x) for x in status_df['status_group'].tolist()]
        
        # 1xx 상태 코드가 없는 경우 강제로 추가 (테스트용)
        if not any(sg for sg in status_groups if sg == 100):
            status_groups.append(100)
        
        return str(status_groups)
    
    return '[]'

@callback(
    Output('status-code-checklist', 'options'),
    Input('status-codes-store', 'children')
)
def update_status_code_options(status_codes_json):
    try:
        if status_codes_json == '[]':
            return [
                {'label': '1xx', 'value': '1xx', 'title': '정보 응답', 'disabled': True},
                {'label': '2xx', 'value': '2xx', 'title': '성공', 'disabled': True},
                {'label': '3xx', 'value': '3xx', 'title': '리다이렉션', 'disabled': True},
                {'label': '4xx', 'value': '4xx', 'title': '클라이언트 오류', 'disabled': True},
                {'label': '5xx', 'value': '5xx', 'title': '서버 오류', 'disabled': True}
            ]
        
        status_codes = eval(status_codes_json)
        
        available_groups = [f"{code//100}xx" for code in status_codes]
        
        updated_options = []
        for option in status_code_groups:
            if option['value'] in available_groups:
                updated_options.append(option)
            else:
                updated_options.append({
                    'label': option['label'],
                    'value': option['value'],
                    'title': option['title'],
                    'disabled': True
                })
        
        return updated_options
    except Exception as e:
        return status_code_groups

@callback(
    Output('status-code-checklist', 'value'),
    [Input('select-all-button', 'n_clicks'),
     Input('clear-all-button', 'n_clicks')],
    [State('status-code-checklist', 'options'),
     State('status-code-checklist', 'value')],
    prevent_initial_call=True
)
def update_checklist_selection(select_clicks, clear_clicks, options, current_values):
    if not ctx.triggered:
        return current_values
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    available_options = [opt['value'] for opt in options if not opt.get('disabled', False)]
    
    if button_id == 'select-all-button':
        return [code for code in ORDERED_STATUS_CODES if code in available_options]
    elif button_id == 'clear-all-button':
        return []
    
    return current_values

@callback(
    Output('status-code-checklist', 'value', allow_duplicate=True),
    [Input('status-code-checklist', 'options')],
    [State('status-code-checklist', 'value')],
    prevent_initial_call=True
)
def update_selected_values(options, current_values):
    if not current_values:
        return ORDERED_STATUS_CODES
    
    available_values = [opt['value'] for opt in options if not opt.get('disabled', False)]
    
    valid_values = []
    for code in ORDERED_STATUS_CODES:
        if code in current_values and code in available_values:
            valid_values.append(code)
    
    if not valid_values and available_values:
        return [code for code in ORDERED_STATUS_CODES if code in available_values]
    
    return valid_values

@callback(
    [Output("pie-normal", "active"),
     Output("pie-log", "active"),
     Output("pie-chart-mode", "data")],
    [Input("pie-normal", "n_clicks"),
     Input("pie-log", "n_clicks")],
    [State("pie-chart-mode", "data")],
    prevent_initial_call=True
)
def update_pie_chart_mode(normal_clicks, log_clicks, current_mode):
    ctx_triggered = ctx.triggered_id
    
    if ctx_triggered == "pie-normal":
        return True, False, "normal"
    elif ctx_triggered == "pie-log":
        return False, True, "log"
    
    return False, True, "log"

@callback(
    [Output("scale-normal", "active"),
     Output("scale-log", "active"),
     Output("scale-normalize", "active"),
     Output("hourly-chart-mode", "data")],
    [Input("scale-normal", "n_clicks"),
     Input("scale-log", "n_clicks"),
     Input("scale-normalize", "n_clicks")],
    [State("hourly-chart-mode", "data")],
    prevent_initial_call=True
)
def update_hourly_chart_mode(normal_clicks, log_clicks, normalize_clicks, current_mode):
    ctx_triggered = ctx.triggered_id
    
    if ctx_triggered == "scale-normal":
        return True, False, False, "normal"
    elif ctx_triggered == "scale-log":
        return False, True, False, "log"
    elif ctx_triggered == "scale-normalize":
        return False, False, True, "percentage"
    
    return False, True, False, "log"

@callback(
    Output('status-distribution-chart', 'figure'),
    [Input('management-start-date', 'date'),
     Input('management-end-date', 'date'),
     Input('pie-chart-mode', 'data')]
)
def update_status_distribution_chart(start_date, end_date, pie_mode):
    if not start_date or not end_date:
        empty_fig = go.Figure().update_layout(title="날짜를 선택해주세요")
        return empty_fig
    
    # 상태 코드 데이터 쿼리
    query = f"""
    SELECT
        status_code,
        FLOOR(status_code/100)*100 AS status_group,
        COUNT(*) as count
    FROM
        `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
    WHERE
        DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY
        status_code, status_group
    """
    
    try:
        df = load_bigquery_data(query)
        if df is None or df.empty:
            empty_fig = go.Figure().update_layout(title="선택한 기간에 데이터가 없습니다")
            return empty_fig
        
        return create_status_distribution_chart(df, ORDERED_STATUS_CODES, pie_mode)
        
    except Exception as e:
        print(f"Error in update_status_distribution_chart: {str(e)}")
        error_fig = go.Figure().update_layout(title=f"오류가 발생했습니다: {str(e)}")
        return error_fig

@callback(
    Output('hourly-status-chart', 'figure'),
    [Input('management-start-date', 'date'),
     Input('management-end-date', 'date'),
     Input('hourly-chart-mode', 'data')]
)
def update_hourly_status_chart(start_date, end_date, hourly_mode):
    if not start_date or not end_date:
        empty_fig = go.Figure().update_layout(title="날짜를 선택해주세요")
        return empty_fig
    
    # 시간별 데이터 쿼리
    query = f"""
    SELECT
        EXTRACT(HOUR FROM timestamp_utc) as hour,
        FLOOR(status_code/100)*100 AS status_group,
        COUNT(*) as count
    FROM
        `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
    WHERE
        DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY
        hour, status_group
    """
    
    try:
        df = load_bigquery_data(query)
        if df is None or df.empty:
            empty_fig = go.Figure().update_layout(title="선택한 기간에 데이터가 없습니다")
            return empty_fig
        
        return create_hourly_status_chart(df, ORDERED_STATUS_CODES, hourly_mode)
        
    except Exception as e:
        print(f"Error in update_hourly_status_chart: {str(e)}")
        error_fig = go.Figure().update_layout(title=f"오류가 발생했습니다: {str(e)}")
        return error_fig

def create_status_distribution_chart(df, sorted_status_codes, chart_mode):
    """상태 코드 분포 차트를 생성합니다."""
    # 상태 코드 그룹별로 집계
    df['status_group_name'] = df['status_group'].apply(lambda x: f"{int(x//100)}xx")
    
    # 그룹별 집계 데이터 생성
    group_df = df.groupby(['status_group_name', 'status_group'])['count'].sum().reset_index()
    
    # 각 그룹별 세부 상태 코드 정보 생성 (툴팁용)
    status_details = {}
    for group in group_df['status_group_name'].unique():
        group_codes = df[df['status_group_name'] == group]
        details = []
        for _, row in group_codes.iterrows():
            details.append(f"상태 코드 {row['status_code']}: {int(row['count']):,}건")
        status_details[group] = "<br>".join(details)
    
    # 파이차트 생성
    fig = go.Figure()
    
    # 상태 코드 그룹 이름 및 색상 목록
    labels = group_df['status_group_name'].tolist()
    
    # 각 그룹의 백분율 계산 (표시용)
    total = group_df['count'].sum()
    percentages = [(count / total) * 100 for count in group_df['count']]
    
    # 실제 차트에 사용할 값
    values = group_df['count'].tolist()
    
    # 로그 스케일 적용 (로그 모드인 경우)
    display_values = values.copy()
    if chart_mode == "log":
        display_values = [max(1, val) for val in display_values]
        display_values = [math.log10(val) for val in display_values]
        min_val = min(display_values)
        if min_val < 1:
            display_values = [val - min_val + 1 for val in display_values]
    
    # 호버 텍스트 생성
    hover_texts = []
    for i, group in enumerate(labels):
        original_count = group_df.loc[group_df['status_group_name'] == group, 'count'].values[0]
        percentage = percentages[i]
        
        detail_text = f"<br><br>세부 상태 코드:<br>{status_details[group]}" if group in status_details else ""
        
        hover_texts.append(
            f"<b>{group}</b><br>총 건수: {original_count:,} ({percentage:.1f}%){detail_text}"
        )
    
    colors = [COLOR_MAP.get(group, '#CCCCCC') for group in labels]
    
    # 파이 차트에 표시할 텍스트 생성
    text_template = '%{label}<br>%{text}%'
    text_values = [f"{p:.1f}" for p in percentages]
    
    # 파이 차트 추가
    fig.add_trace(go.Pie(
        labels=labels,
        values=display_values,
        text=text_values,
        texttemplate=text_template,
        hovertemplate='%{customdata}<extra></extra>',
        customdata=hover_texts,
        textinfo='label+text',
        marker_colors=colors,
        hole=0.4,
        sort=False,
        direction='clockwise',
        pull=[0.03] * len(labels),
        textposition='inside'
    ))
    
    # 차트 모드에 따른 제목 설정
    title_suffix = " (로그 스케일)" if chart_mode == "log" else ""
    
    # 제목 및 레이아웃 설정
    selected_codes_str = ', '.join(sorted_status_codes)
    fig.update_layout(
        title=f"HTTP 상태 코드 분포{title_suffix}",
        showlegend=True,
        legend_title="상태 코드",
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=80, b=30 if chart_mode == "log" else 20, l=20, r=20),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12
        )
    )
    
    return fig

def create_hourly_status_chart(df, sorted_status_codes, chart_mode):
    """시간별 상태 코드 차트를 생성합니다."""
    # 모든 시간대에 대해 데이터 초기화 (0-23시)
    hour_range = list(range(24))
    
    # 상태 코드 그룹별로 데이터 준비
    df['status_group_name'] = df['status_group'].apply(lambda x: f"{int(x//100)}xx")
    
    # 피벗 테이블 생성
    pivot_df = df.pivot_table(
        values='count',
        index='hour',
        columns='status_group_name',
        fill_value=0
    ).reset_index()
    
    # 누락된 시간대 추가
    full_df = pd.DataFrame({'hour': hour_range})
    pivot_df = pd.merge(full_df, pivot_df, on='hour', how='left').fillna(0)
    
    fig = go.Figure()
    
    # 각 상태 코드 그룹에 대한 바 추가
    for code in sorted_status_codes:
        group_name = f"{code[0]}xx"
        if group_name in pivot_df.columns:
            values = pivot_df[group_name]
            
            # 백분율 모드인 경우 데이터 변환
            if chart_mode == "percentage":
                row_sums = pivot_df[[col for col in pivot_df.columns if col != 'hour']].sum(axis=1)
                values = (values / row_sums * 100).fillna(0)
            
            fig.add_trace(go.Bar(
                x=pivot_df['hour'],
                y=values,
                name=group_name,
                marker_color=COLOR_MAP.get(group_name, '#CCCCCC')
            ))
    
    # 차트 모드에 따른 제목 및 Y축 레이블 설정
    if chart_mode == "log":
        title_suffix = " (로그 스케일)"
        y_axis_title = "요청 수 (로그)"
    elif chart_mode == "percentage":
        title_suffix = " (백분율)"
        y_axis_title = "비율 (%)"
    else:
        title_suffix = ""
        y_axis_title = "요청 수"
    
    # 제목 설정
    fig.update_layout(
        title=f"시간대별 상태 코드 분포{title_suffix}",
        barmode='stack' if chart_mode == "percentage" else 'group',
        xaxis=dict(
            title="시간",
            tickmode='array',
            tickvals=list(range(0, 24)),
            ticktext=[f"{h:02d}:00" for h in range(0, 24)]
        ),
        yaxis=dict(
            title=y_axis_title,
            type='log' if chart_mode == "log" else 'linear',
            range=[0, 100] if chart_mode == "percentage" else None
        ),
        hovermode="x unified",
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=80, b=30 if chart_mode == "log" else 20, l=20, r=20),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12
        )
    )
    
    return fig

def get_error_ip_data(start_date, end_date, error_type):
    """오류 IP 데이터를 조회합니다."""
    if not start_date or not end_date:
        return []
    
    query = f"""
    SELECT
        ip,
        COUNT(*) as request_count,
        ANY_VALUE(geo) as geo
    FROM
        `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
    WHERE
        DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
        AND CAST(status_code AS INT64) BETWEEN {error_type}00 AND {error_type}99
    GROUP BY
        ip
    ORDER BY
        request_count DESC
    LIMIT 10
    """
    
    df = load_bigquery_data(query)
    data = []
    
    if not df.empty:
        for i, row in df.iterrows():
            data.append({
                "rank": i + 1,
                "ip": row["ip"],
                "count": f"{int(row['request_count']):,}",
                "geo": row["geo"]
            })
    
    return data

@callback(
    [Output('4xx-ips-table', 'data'),
     Output('5xx-ips-table', 'data')],
    [Input('management-start-date', 'date'),
     Input('management-end-date', 'date')]
)
def update_error_ip_tables(start_date, end_date):
    if not start_date or not end_date:
        return [], []
    
    data_4xx = get_error_ip_data(start_date, end_date, '4')
    data_5xx = get_error_ip_data(start_date, end_date, '5')
    
    return data_4xx, data_5xx

@callback(
    [Output('log-search-table', 'data'),
     Output('log-search-info', 'children'),
     Output('log-search-table', 'page_count')],
    [Input('log-search-button', 'n_clicks'),
     Input('log-search-table', 'page_current'),
     Input('log-search-table', 'page_size'),
     Input('log-search-table', 'sort_by')],
    [State('log-search-start-date', 'date'),
     State('log-search-start-time', 'value'),
     State('log-search-end-date', 'date'),
     State('log-search-end-time', 'value'),
     State('log-search-ip', 'value'),
     State('log-search-url', 'value'),
     State('log-search-geo', 'value'),
     State('log-search-user-agent', 'value')]
)
def update_log_search_table(n_clicks, page_current, page_size, sort_by, 
                          start_date, start_time, end_date, end_time, 
                          ip_filter, url_filter, geo_filter, user_agent_filter):
    if not n_clicks:
        return [], "", 0
    
    if not start_date or not end_date:
        return [], "", 0
    
    # 날짜와 시간을 결합하여 timestamp 생성 (UTC 기준)
    start_datetime = f"{start_date} {start_time}:00.000000 UTC"
    end_datetime = f"{end_date} {end_time}:59.999999 UTC"
    
    # 검색 조건 생성
    conditions = [
        f"timestamp_utc >= '{start_datetime}'",
        f"timestamp_utc <= '{end_datetime}'"
    ]
    
    # 추가 검색 조건
    if ip_filter:
        conditions.append(f"LOWER(ip) LIKE LOWER('%{ip_filter}%')")
    if url_filter:
        conditions.append(f"LOWER(url) LIKE LOWER('%{url_filter}%')")
    if geo_filter:
        conditions.append(f"LOWER(geo) LIKE LOWER('%{geo_filter}%')")
    if user_agent_filter:
        conditions.append(f"""(
            LOWER(user_browser) LIKE LOWER('%{user_agent_filter}%')
            OR LOWER(user_os) LIKE LOWER('%{user_agent_filter}%')
            OR LOWER(user_agent) LIKE LOWER('%{user_agent_filter}%')
        )""")
    
    # WHERE 절 생성
    where_clause = " AND ".join(conditions)
    
    # 정렬 조건
    order_by = "timestamp_utc DESC"  # 기본 정렬
    if sort_by:
        sort = sort_by[0]
        column = sort['column_id']
        direction = "DESC" if sort['direction'] == 'desc' else "ASC"
        
        # 컬럼명 매핑
        column_mapping = {
            'timestamp': 'timestamp_utc',
            'status_code': 'CAST(status_code AS INT64)',
            'ip': 'ip',
            'url': 'url',
            'geo': 'geo',
            'http_method': 'http_method',
            'user_browser': 'user_browser',
            'user_os': 'user_os',
            'user_is_mobile': 'user_is_mobile',
            'user_is_bot': 'user_is_bot'
        }
        
        if column in column_mapping:
            order_by = f"{column_mapping[column]} {direction}"
    
    try:
        # 최근 1000개 데이터 조회
        data_query = f"""
        SELECT
            ip,
            status_code,
            timestamp_utc as timestamp,
            url,
            geo,
            http_method,
            user_agent,
            user_browser,
            user_os,
            user_is_mobile,
            user_is_bot
        FROM
            `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
        WHERE
            {where_clause}
        ORDER BY
            {order_by}
        LIMIT 1000
        """
        
        df = load_bigquery_data(data_query)
        if df is None or df.empty:
            return [], "검색 결과가 없습니다.", 0
        
        # 데이터 포맷팅
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 현재 페이지의 데이터 추출
        start_idx = page_current * page_size
        end_idx = min((page_current + 1) * page_size, len(df))
        current_page_data = df.iloc[start_idx:end_idx]
        
        # 페이지네이션 정보
        total_count = len(df)
        start_idx = page_current * page_size + 1
        end_idx = min((page_current + 1) * page_size, total_count)
        info_text = f"최근 {total_count:,}개 데이터 중 {start_idx:,} - {end_idx:,}건 표시"
        
        # 총 페이지 수 계산 (올림 처리)
        page_count = (total_count + page_size - 1) // page_size
        
        return current_page_data.to_dict('records'), info_text, page_count
    except Exception as e:
        print(f"Error in update_log_search_table: {str(e)}")
        return [], f"오류가 발생했습니다: {str(e)}", 0

@callback(
    [Output("2xx-count", "children"),
     Output("3xx-count", "children"),
     Output("4xx-count", "children"),
     Output("5xx-count", "children")],
    [Input('management-start-date', 'date'),
     Input('management-end-date', 'date')]
)
def update_status_code_counts(start_date, end_date):
    if not start_date or not end_date:
        return "0", "0", "0", "0"
    
    query = f"""
    SELECT
        FLOOR(status_code/100)*100 AS status_group,
        COUNT(*) as count
    FROM
        `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
    WHERE
        DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
    GROUP BY
        status_group
    ORDER BY
        status_group
    """
    
    try:
        df = load_bigquery_data(query)
        if df is None or df.empty:
            return "0", "0", "0", "0"
        
        # 상태 코드 그룹별 카운트 추출
        counts = {int(row['status_group']): f"{int(row['count']):,}" for _, row in df.iterrows()}
        
        return (
            counts.get(200, "0"),  # 2xx
            counts.get(300, "0"),  # 3xx
            counts.get(400, "0"),  # 4xx
            counts.get(500, "0")   # 5xx
        )
        
    except Exception as e:
        print(f"Error in update_status_code_counts: {str(e)}")
        return "0", "0", "0", "0"

# 페이지 레이아웃 정의
layout = create_management_layout() 