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

def create_management_layout():
    """관리 페이지 레이아웃을 생성합니다."""
    return html.Div([
        html.H2("관리"),
        html.Div([
            # 필터 섹션
            html.Div([
                dbc.Row([
                    # 날짜 선택기
                    dbc.Col([
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
                            ], style={"display": "inline-block"}),
                        ], style={"display": "flex", "alignItems": "center", "marginTop": "5px"})
                    ], width=6),
                    # 상태 코드 필터
                    dbc.Col([
                        html.Label("HTTP 상태 코드", className="filter-label"),
                        html.Div([
                            dcc.Checklist(
                                id='status-code-checklist',
                                options=status_code_groups,
                                value=ORDERED_STATUS_CODES,
                                inline=True,
                                className="status-code-checklist",
                                inputStyle={"marginRight": "5px"},
                                labelStyle={
                                    "marginRight": "15px",
                                    "padding": "6px 10px",
                                    "borderRadius": "25px",
                                    "display": "inline-flex",
                                    "alignItems": "center",
                                    "fontWeight": "500"
                                }
                            ),
                            html.Button(
                                "모두 선택",
                                id="select-all-button",
                                className="select-button",
                                style={
                                    "marginLeft": "10px",
                                    "fontSize": "0.8rem",
                                    "padding": "3px 8px",
                                    "backgroundColor": "#f8f9fa",
                                    "border": "1px solid #dee2e6",
                                    "borderRadius": "4px",
                                    "cursor": "pointer"
                                }
                            ),
                            html.Button(
                                "선택 해제",
                                id="clear-all-button",
                                className="select-button",
                                style={
                                    "marginLeft": "5px",
                                    "fontSize": "0.8rem",
                                    "padding": "3px 8px",
                                    "backgroundColor": "#f8f9fa",
                                    "border": "1px solid #dee2e6",
                                    "borderRadius": "4px",
                                    "cursor": "pointer"
                                }
                            )
                        ], style={
                            "display": "flex",
                            "alignItems": "center",
                            "marginTop": "5px",
                            "marginBottom": "15px",
                            "padding": "8px 12px",
                            "backgroundColor": "#f8f9fa",
                            "borderRadius": "8px",
                            "border": "1px solid #e9ecef"
                        })
                    ], width=6)
                ])
            ], className="filter-container"),
            
            # 메인 차트 섹션
            html.Div([
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
                html.Hr(style={"margin": "30px 0 20px 0"}),
                html.H3("오류 발생 IP 분석", style={"marginBottom": "20px"}),
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H4("4xx 오류 발생 TOP 10 IP", style={"marginBottom": "10px"}),
                            dcc.Loading(
                                id="loading-4xx-ips",
                                type="circle",
                                children=dash_table.DataTable(
                                    id="4xx-ips-table",
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
                    ], width=6),
                    dbc.Col([
                        html.Div([
                            html.H4("5xx 오류 발생 TOP 10 IP", style={"marginBottom": "10px"}),
                            dcc.Loading(
                                id="loading-5xx-ips",
                                type="circle",
                                children=dash_table.DataTable(
                                    id="5xx-ips-table",
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
                    ], width=6)
                ])
            ], className="detail-container"),
        ], className="page-container"),
        
        # 데이터 저장용 숨겨진 div
        html.Div(id='status-codes-store', style={'display': 'none'})
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
    Output('status-distribution-chart', 'figure'),
    [Input('management-start-date', 'date'),
     Input('management-end-date', 'date'),
     Input('status-code-checklist', 'value'),
     Input('pie-chart-mode', 'data')]
)
def update_status_distribution_chart(start_date, end_date, status_codes, chart_mode):
    if not start_date or not end_date:
        return go.Figure().update_layout(title="날짜를 선택해주세요")
    
    if not status_codes:
        return go.Figure().update_layout(title="상태 코드를 선택해주세요")
    
    sorted_status_codes = [code for code in ORDERED_STATUS_CODES if code in status_codes]
    
    # 상태 코드 필터 조건 생성
    status_filters = []
    for code in sorted_status_codes:
        status_group = int(code[0]) * 100
        status_filters.append(f"status_code BETWEEN {status_group} AND {status_group + 99}")
    
    status_filter = f"AND ({' OR '.join(status_filters)})" if status_filters else ""
    
    query = f"""
    SELECT
        status_code,
        FLOOR(status_code/100)*100 AS status_group,
        COUNT(*) as count
    FROM
        `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
    WHERE
        DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
        {status_filter}
    GROUP BY
        status_code, status_group
    ORDER BY
        status_code
    """
    
    df = load_bigquery_data(query)
    
    if df.empty:
        return go.Figure().update_layout(title="선택한 기간에 데이터가 없습니다")
    
    # 상태 코드 그룹별로 집계
    df['status_group_name'] = df['status_group'].apply(lambda x: f"{int(x//100)}xx")
    
    # 그룹별 집계 데이터 생성
    group_df = df.groupby('status_group_name').agg(
        total_count=('count', 'sum')
    ).reset_index()
    
    # 각 그룹별 세부 상태 코드 정보 생성 (툴팁용)
    status_details = {}
    for group in group_df['status_group_name'].unique():
        group_codes = df[df['status_group_name'] == group]
        details = []
        for _, row in group_codes.iterrows():
            details.append(f"상태 코드 {int(row['status_code'])}: {int(row['count'])}건")
        status_details[group] = "<br>".join(details)
    
    # 파이차트 생성
    fig = go.Figure()
    
    # 상태 코드 그룹 이름 및 색상 목록
    labels = group_df['status_group_name'].tolist()
    
    # 각 그룹의 백분율 계산 (표시용)
    total = sum(group_df['total_count'])
    percentages = [(count / total) * 100 for count in group_df['total_count']]
    
    # 실제 차트에 사용할 값
    values = group_df['total_count'].tolist()
    
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
        original_count = group_df.loc[group_df['status_group_name'] == group, 'total_count'].values[0]
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
    title_suffix = " (로그 스케일, 실제 백분율 표시)" if chart_mode == "log" else ""
    
    # 제목 및 레이아웃 설정
    selected_codes_str = ', '.join(sorted_status_codes)
    fig.update_layout(
        title=f"상태 코드 분포 ({selected_codes_str}){title_suffix}",
        showlegend=True,
        legend_title="상태 코드 그룹",
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
def update_chart_mode(normal_clicks, log_clicks, normalize_clicks, current_mode):
    ctx_triggered = ctx.triggered_id
    
    if ctx_triggered == "scale-normal":
        return True, False, False, "normal"
    elif ctx_triggered == "scale-log":
        return False, True, False, "log"
    elif ctx_triggered == "scale-normalize":
        return False, False, True, "percentage"
    
    return False, True, False, "log"

@callback(
    Output('hourly-status-chart', 'figure'),
    [Input('management-start-date', 'date'),
     Input('management-end-date', 'date'),
     Input('status-code-checklist', 'value'),
     Input('hourly-chart-mode', 'data')]
)
def update_hourly_status_chart(start_date, end_date, status_codes, chart_mode):
    if not start_date or not end_date:
        return go.Figure().update_layout(title="날짜를 선택해주세요")
    
    if not status_codes:
        return go.Figure().update_layout(title="상태 코드를 선택해주세요")
    
    sorted_status_codes = [code for code in ORDERED_STATUS_CODES if code in status_codes]
    
    # 모든 시간대에 대해 데이터 초기화 (0-23시)
    hour_range = list(range(24))
    
    # 다중 상태 코드 그룹의 경우 각 그룹별로 데이터 조회
    fig = go.Figure()
    all_data = {}  # 정규화를 위한 모든 데이터 저장
    
    for code in sorted_status_codes:
        status_group = int(code[0]) * 100
        
        # 시간별 요청 수 조회 쿼리
        query = f"""
        SELECT
            EXTRACT(HOUR FROM timestamp_utc) as hour,
            COUNT(*) as request_count
        FROM
            `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
        WHERE
            DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
            AND status_code BETWEEN {status_group} AND {status_group + 99}
        GROUP BY
            hour
        ORDER BY
            hour
        """
        
        df = load_bigquery_data(query)
        
        # 결과 데이터가 모든 시간대를 포함하지 않을 수 있으므로 빈 데이터프레임으로 초기화
        full_df = pd.DataFrame({'hour': hour_range, 'request_count': [0] * 24})
        
        # 쿼리 결과가 있으면 병합
        if not df.empty:
            df['hour'] = df['hour'].astype(int)
            
            # 쿼리 결과와 기본 데이터프레임 병합
            for _, row in df.iterrows():
                full_df.loc[full_df['hour'] == row['hour'], 'request_count'] = row['request_count']
        
        # 모든 데이터 저장 (정규화용)
        all_data[code] = full_df
    
    # 차트 모드에 따라 데이터 처리 (백분율 모드)
    if chart_mode == "percentage" and len(all_data) > 1:
        for hour in hour_range:
            total_for_hour = sum(all_data[code].loc[all_data[code]['hour'] == hour, 'request_count'].values[0] for code in sorted_status_codes)
            if total_for_hour > 0:
                for code in sorted_status_codes:
                    count = all_data[code].loc[all_data[code]['hour'] == hour, 'request_count'].values[0]
                    all_data[code].loc[all_data[code]['hour'] == hour, 'request_count'] = (count / total_for_hour) * 100
    
    # 데이터가 있는지 확인
    has_data = False
    
    # 각 상태 코드 그룹에 대한 바 추가
    for code in sorted_status_codes:
        df = all_data[code]
        
        if df['request_count'].sum() > 0:
            has_data = True
            
            # 각 상태 코드 그룹별로 바 추가
            fig.add_trace(go.Bar(
                x=df['hour'],
                y=df['request_count'],
                name=code,
                marker_color=COLOR_MAP.get(code, '#CCCCCC')
            ))
    
    if not has_data:
        return go.Figure().update_layout(title="선택한 기간에 데이터가 없습니다")
    
    # 차트 모드에 따른 제목 및 Y축 레이블 설정
    if chart_mode == "log":
        title_suffix = " (로그 스케일)"
        y_axis_title = "요청 수 (로그 스케일)"
    elif chart_mode == "percentage":
        title_suffix = " (백분율)"
        y_axis_title = "백분율 (%)"
    else:
        title_suffix = ""
        y_axis_title = "요청 수"
    
    # 제목 설정
    fig.update_layout(
        title=f"시간별 요청 수 ({', '.join(sorted_status_codes)}){title_suffix}",
        barmode='stack' if chart_mode == "percentage" else 'group',
        xaxis=dict(
            title="시간대",
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

@callback(
    [Output('4xx-ips-table', 'data'),
     Output('5xx-ips-table', 'data')],
    [Input('management-start-date', 'date'),
     Input('management-end-date', 'date'),
     Input('status-code-checklist', 'value')]
)
def update_error_ip_tables(start_date, end_date, status_codes):
    if not start_date or not end_date:
        return [], []
    
    if not status_codes or not ('4xx' in status_codes or '5xx' in status_codes):
        return [], []
    
    # 4xx 에러 발생 IP 조회
    data_4xx = []
    if '4xx' in status_codes:
        query_4xx = f"""
        SELECT
            ip,
            COUNT(*) as request_count,
            ANY_VALUE(geo) as geo
        FROM
            `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
        WHERE
            DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
            AND CAST(status_code AS INT64) BETWEEN 400 AND 499
        GROUP BY
            ip
        ORDER BY
            request_count DESC
        LIMIT 10
        """
        
        df_4xx = load_bigquery_data(query_4xx)
        
        if not df_4xx.empty:
            for i, row in df_4xx.iterrows():
                data_4xx.append({
                    "rank": i + 1,
                    "ip": row["ip"],
                    "count": f"{int(row['request_count']):,}",
                    "geo": row["geo"]
                })
    
    # 5xx 에러 발생 IP 조회
    data_5xx = []
    if '5xx' in status_codes:
        query_5xx = f"""
        SELECT
            ip,
            COUNT(*) as request_count,
            ANY_VALUE(geo) as geo
        FROM
            `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
        WHERE
            DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
            AND CAST(status_code AS INT64) BETWEEN 500 AND 599
        GROUP BY
            ip
        ORDER BY
            request_count DESC
        LIMIT 10
        """
        
        df_5xx = load_bigquery_data(query_5xx)
        
        if not df_5xx.empty:
            for i, row in df_5xx.iterrows():
                data_5xx.append({
                    "rank": i + 1,
                    "ip": row["ip"],
                    "count": f"{int(row['request_count']):,}",
                    "geo": row["geo"]
                })
    
    return data_4xx, data_5xx

# 페이지 레이아웃 정의
layout = create_management_layout() 