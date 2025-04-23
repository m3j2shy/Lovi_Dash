from dash import html, dcc, callback, Output, Input, State, ctx
import dash_bootstrap_components as dbc
from utils.utils import load_bigquery_data
import pandas as pd
import datetime
import plotly.express as px
import plotly.graph_objects as go
import math

# BigQuery에서 날짜 데이터 조회
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

# 날짜 데이터를 datetime.date 객체로 변환 및 범위 설정
if not query_result.empty:
    query_result['date'] = pd.to_datetime(query_result['date']).dt.date
    
    # 최소 날짜와 최대 날짜 찾기
    min_date = query_result['date'].min()
    max_date = query_result['date'].max()
    
    # 날짜를 문자열로 변환 (YYYY-MM-DD 형식)
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
                    # 상태 코드 필터 (체크박스로 변경)
                    dbc.Col([
                        html.Label("HTTP 상태 코드", className="filter-label"),
                        html.Div([
                            dcc.Checklist(
                                id='status-code-checklist',
                                options=status_code_groups,
                                value=['1xx', '2xx', '3xx', '4xx', '5xx'],  # 기본적으로 모든 옵션 선택
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
            
            # 메인 차트 섹션 - 상태 코드 분포 및 시간별 상태 코드
            html.Div([
                dbc.Row([
                    # 상태 코드 분포 차트
                    dbc.Col([
                        html.Div([
                            html.H4("상태 코드 분포", style={"marginBottom": "5px"}),
                            # 파이 차트 표시 옵션 추가
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
                        # 파이 차트 표시 방식 저장용 (hidden)
                        dcc.Store(id='pie-chart-mode', data='log')
                    ], width=6),
                    # 시간별 상태 코드 차트
                    dbc.Col([
                        html.Div([
                            html.H4("시간별 상태 코드", style={"marginBottom": "5px"}),
                            # 차트 표시 옵션 추가
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
                        # 차트 표시 방식 저장용 (hidden)
                        dcc.Store(id='hourly-chart-mode', data='log')
                    ], width=6)
                ])
            ], className="main-container"),
            
            # 세부 정보 섹션 - 일별 요청 수
            html.Div([
                html.H4("일별 요청 수"),
                dcc.Loading(
                    id="loading-system-status",
                    type="circle",
                    children=dcc.Graph(id='system-status-chart')
                )
            ], className="detail-container")
        ], className="page-container"),
        
        # 데이터 저장을 위한 숨겨진 div
        html.Div(id='status-codes-store', style={'display': 'none'})
    ])

# 초기 상태 코드 데이터 조회 (앱 시작 시)
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

# 선택한 날짜 범위에 따라 상태 코드 데이터를 조회하는 콜백
@callback(
    Output('status-codes-store', 'children'),
    [Input('management-start-date', 'date'),
     Input('management-end-date', 'date')]
)
def query_status_codes(start_date, end_date):
    if not start_date or not end_date:
        print(f"초기 상태 코드 그룹: {initial_status_groups}")
        return str(initial_status_groups)  # 초기값 사용
    
    # BigQuery에서 해당 기간의 상태 코드 데이터 조회
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
    
    # 결과를 JSON 형식으로 반환
    if not status_df.empty:
        status_groups = [int(x) for x in status_df['status_group'].tolist()]
        print(f"조회된 상태 코드 그룹: {status_groups}")
        
        # 1xx 상태 코드가 없는 경우 강제로 추가 (개발 시 테스트용)
        if not any(sg for sg in status_groups if sg == 100):
            print("1xx 상태 코드를 표시하기 위해 강제로 추가합니다")
            status_groups.append(100)
        
        return str(status_groups)
    
    return '[]'

# 상태 코드 데이터에 따라 체크박스 옵션을 업데이트하는 콜백
@callback(
    Output('status-code-checklist', 'options'),
    Input('status-codes-store', 'children')
)
def update_status_code_options(status_codes_json):
    try:
        if status_codes_json == '[]':
            # 데이터가 없으면 모든 옵션을 비활성화
            return [
                {'label': '1xx', 'value': '1xx', 'title': '정보 응답', 'disabled': True},
                {'label': '2xx', 'value': '2xx', 'title': '성공', 'disabled': True},
                {'label': '3xx', 'value': '3xx', 'title': '리다이렉션', 'disabled': True},
                {'label': '4xx', 'value': '4xx', 'title': '클라이언트 오류', 'disabled': True},
                {'label': '5xx', 'value': '5xx', 'title': '서버 오류', 'disabled': True}
            ]
        
        # 문자열을 리스트로 변환
        status_codes = eval(status_codes_json)
        print(f"업데이트할 상태 코드 옵션: {status_codes}")
        
        # 상태 코드 그룹 매핑
        available_groups = []
        for code in status_codes:
            group = f"{code//100}xx"
            available_groups.append(group)
        
        print(f"사용 가능한 그룹: {available_groups}")
        
        # 옵션 업데이트 - 존재하는 그룹은 활성화, 없는 그룹은 비활성화
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
        print(f"상태 코드 옵션 업데이트 중 오류: {e}")
        return status_code_groups

# 모두 선택/해제 버튼 콜백
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
    
    # 활성화된 옵션만 필터링
    available_options = [opt['value'] for opt in options if not opt.get('disabled', False)]
    
    # 정렬된 상태 코드 순서
    ordered_status_codes = ['1xx', '2xx', '3xx', '4xx', '5xx']
    
    if button_id == 'select-all-button':
        # 모든 활성화된 옵션 선택 (정렬된 순서 유지)
        return [code for code in ordered_status_codes if code in available_options]
    elif button_id == 'clear-all-button':
        # 모든 선택 해제
        return []
    
    return current_values

# 체크박스 값이 변경될 때 선택된 값 유지하는 콜백
@callback(
    Output('status-code-checklist', 'value', allow_duplicate=True),
    [Input('status-code-checklist', 'options')],
    [State('status-code-checklist', 'value')],
    prevent_initial_call=True
)
def update_selected_values(options, current_values):
    if not current_values:
        # 선택된 값이 없으면 기본값 반환
        ordered_status_codes = ['1xx', '2xx', '3xx', '4xx', '5xx']
        return ordered_status_codes
    
    # 사용 가능한 옵션 확인
    available_values = [opt['value'] for opt in options if not opt.get('disabled', False)]
    
    # 정렬된 상태 코드 순서
    ordered_status_codes = ['1xx', '2xx', '3xx', '4xx', '5xx']
    
    # 선택된 값을 정렬된 순서로 재정렬
    valid_values = []
    for code in ordered_status_codes:
        if code in current_values and code in available_values:
            valid_values.append(code)
    
    # 선택된 값이 없으면 사용 가능한 모든 값 반환 (정렬된 순서로)
    if not valid_values and available_values:
        return [code for code in ordered_status_codes if code in available_values]
    
    return valid_values

# 일별 요청 수 차트 업데이트 콜백
@callback(
    Output('system-status-chart', 'figure'),
    [Input('management-start-date', 'date'),
     Input('management-end-date', 'date'),
     Input('status-code-checklist', 'value')]
)
def update_system_status_chart(start_date, end_date, status_codes):
    if not start_date or not end_date:
        return go.Figure().update_layout(title="날짜를 선택해주세요")
    
    if not status_codes:
        return go.Figure().update_layout(title="상태 코드를 선택해주세요")
    
    # 상태 코드 정렬
    ordered_status_codes = ['1xx', '2xx', '3xx', '4xx', '5xx']
    sorted_status_codes = [code for code in ordered_status_codes if code in status_codes]
    
    # 상태 코드 필터 조건 생성
    status_filters = []
    for code in sorted_status_codes:
        status_group = int(code[0]) * 100  # 첫 번째 문자를 정수로 변환 후 100 곱함 (2xx -> 200)
        status_filters.append(f"status_code BETWEEN {status_group} AND {status_group + 99}")
    
    # 1xx 상태 코드가 포함된 경우의 특별 처리
    if '1xx' in sorted_status_codes and all(code != '1xx' for code in sorted_status_codes):
        # 1xx만 선택된 경우 빈 데이터프레임 생성
        df = pd.DataFrame(columns=['date', 'request_count'])
        fig = go.Figure()
        fig.add_annotation(
            text="현재 1xx 상태 코드 데이터가 없습니다",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            title=f"일별 요청 수 ({', '.join(sorted_status_codes)})",
            xaxis_title="날짜",
            yaxis_title="요청 수",
            template="plotly_white"
        )
        return fig
    
    status_filter = f"AND ({' OR '.join(status_filters)})" if status_filters else ""
    
    # 일별 요청 수 조회 쿼리
    query = f"""
    SELECT
        DATE(timestamp_utc) as date,
        COUNT(*) as request_count
    FROM
        `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
    WHERE
        DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
        {status_filter}
    GROUP BY
        date
    ORDER BY
        date
    """
    
    df = load_bigquery_data(query)
    
    if df.empty:
        return go.Figure().update_layout(title="선택한 기간에 데이터가 없습니다")
    
    # 일별 요청 수 차트 생성 (막대 그래프)
    fig = px.bar(
        df, 
        x='date', 
        y='request_count', 
        title=f"일별 요청 수 ({', '.join(sorted_status_codes)})",
        labels={'date': '날짜', 'request_count': '요청 수'},
        color_discrete_sequence=['#3366CC']
    )
    
    fig.update_layout(
        xaxis_title="날짜",
        yaxis_title="요청 수",
        hovermode="x unified",
        template="plotly_white",
        bargap=0.2,
        margin=dict(t=80, b=20, l=20, r=20),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12
        )
    )
    
    return fig

# 파이 차트 스케일 모드 버튼 콜백
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
    
    # 기본값 유지
    return False, True, "log"

# 상태 코드 분포 차트 업데이트 콜백
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
    
    # 상태 코드 정렬
    ordered_status_codes = ['1xx', '2xx', '3xx', '4xx', '5xx']
    sorted_status_codes = [code for code in ordered_status_codes if code in status_codes]
    
    # 상태 코드 필터 조건 생성
    status_filters = []
    for code in sorted_status_codes:
        status_group = int(code[0]) * 100  # 첫 번째 문자를 정수로 변환 후 100 곱함 (2xx -> 200)
        status_filters.append(f"status_code BETWEEN {status_group} AND {status_group + 99}")
    
    status_filter = f"AND ({' OR '.join(status_filters)})" if status_filters else ""
    
    # 상태 코드별 분포 조회 쿼리 - 개별 상태 코드와 그룹 정보 함께 가져오기
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
    df['status_group_name'] = df['status_group'].apply(
        lambda x: f"{int(x//100)}xx"
    )
    
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
    
    # 그룹별 색상 매핑 정의
    color_map = {
        '1xx': '#9C27B0',  # 정보 응답 - 보라색
        '2xx': '#66BB6A',  # 성공 - 녹색
        '3xx': '#42A5F5',  # 리다이렉션 - 파란색
        '4xx': '#FFA726',  # 클라이언트 오류 - 주황색
        '5xx': '#EF5350'   # 서버 오류 - 빨간색
    }
    
    # 파이차트 생성
    fig = go.Figure()
    
    # 선택한 상태 코드에 따라 파이 차트 생성
    # 상태 코드 그룹 이름 및 색상 목록
    labels = group_df['status_group_name'].tolist()
    
    # 각 그룹의 백분율 계산 (표시용)
    total = sum(group_df['total_count'])
    percentages = [(count / total) * 100 for count in group_df['total_count']]
    
    # 실제 차트에 사용할 값
    values = group_df['total_count'].tolist()
    
    # 로그 스케일 적용 (로그 모드인 경우 시각화 목적으로만 사용)
    display_values = values.copy()
    if chart_mode == "log":
        # 값이 0인 경우 1로 대체 (로그 스케일에서 0은 -Infinity가 됨)
        display_values = [max(1, val) for val in display_values]
        # 로그 변환 적용 (base-10)
        display_values = [math.log10(val) for val in display_values]
        # 값이 너무 작은 경우를 방지하기 위해 최소값 설정
        min_val = min(display_values)
        if min_val < 1:
            display_values = [val - min_val + 1 for val in display_values]
    
    # 호버 텍스트 생성
    hover_texts = []
    for i, group in enumerate(labels):
        original_count = group_df.loc[group_df['status_group_name'] == group, 'total_count'].values[0]
        percentage = percentages[i]
        
        if group in status_details:
            detail_text = f"<br><br>세부 상태 코드:<br>{status_details[group]}"
        else:
            detail_text = ""
            
        hover_texts.append(
            f"<b>{group}</b><br>총 건수: {original_count:,} ({percentage:.1f}%){detail_text}"
        )
    
    colors = [color_map.get(group, '#CCCCCC') for group in labels]
    
    # 파이 차트에 표시할 텍스트 생성
    # 로그 모드에서도 실제 백분율 표시
    text_template = '%{label}<br>%{text}%'
    text_values = [f"{p:.1f}" for p in percentages]
    
    # 파이 차트 추가
    fig.add_trace(go.Pie(
        labels=labels,
        values=display_values,  # 로그 스케일 변환 값 (시각화용)
        text=text_values,  # 실제 백분율 (표시용)
        texttemplate=text_template,
        hovertemplate='%{customdata}<extra></extra>',
        customdata=hover_texts,
        textinfo='label+text',  # text 필드를 사용
        marker_colors=colors,
        hole=0.4,
        sort=False,
        direction='clockwise',
        pull=[0.03] * len(labels),
        textposition='inside'
    ))
    
    # 차트 모드에 따른 제목 설정
    title_suffix = " (로그 스케일, 실제 백분율 표시)" if chart_mode == "log" else ""
    
    # 제목 및 레이아웃 설정 - 정렬된 상태 코드 사용
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
        )
    )
    
    # 로그 스케일 모드인 경우 추가 여백과 안내 메시지
    if chart_mode == "log":
        fig.update_layout(
            margin=dict(t=80, b=30, l=20, r=20),
            hoverlabel=dict(
                bgcolor="white",
                font_size=12
            )
        )
    else:
        # 일반 모드에서도 여백과 호버 레이블 설정
        fig.update_layout(
            margin=dict(t=80, b=20, l=20, r=20),
            hoverlabel=dict(
                bgcolor="white",
                font_size=12
            )
        )
    
    return fig

# 차트 스케일 모드 버튼 콜백
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
    
    # 기본값 유지
    return False, True, False, "log"

# 시간별 상태 코드 차트 업데이트 콜백
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
    
    # 상태 코드 정렬
    ordered_status_codes = ['1xx', '2xx', '3xx', '4xx', '5xx']
    sorted_status_codes = [code for code in ordered_status_codes if code in status_codes]
    
    # 상태 코드 그룹별 색상 매핑 정의
    color_map = {
        '1xx': '#9C27B0',  # 정보 응답 - 보라색
        '2xx': '#66BB6A',  # 성공 - 녹색
        '3xx': '#42A5F5',  # 리다이렉션 - 파란색
        '4xx': '#FFA726',  # 클라이언트 오류 - 주황색
        '5xx': '#EF5350'   # 서버 오류 - 빨간색
    }
    
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
            # 시간을 정수로 변환
            df['hour'] = df['hour'].astype(int)
            
            # 쿼리 결과와 기본 데이터프레임 병합
            for _, row in df.iterrows():
                full_df.loc[full_df['hour'] == row['hour'], 'request_count'] = row['request_count']
        
        # 모든 데이터 저장 (정규화용)
        all_data[code] = full_df
    
    # 차트 모드에 따라 데이터 처리
    if chart_mode == "percentage" and len(all_data) > 1:
        # 백분율 모드: 각 시간대별로 백분율로 표시
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
                marker_color=color_map.get(code, '#CCCCCC')
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
        barmode='stack' if chart_mode == "percentage" else 'group'
    )
    
    # y축 로그 스케일 적용 (로그 모드인 경우)
    yaxis_config = {
        'title': y_axis_title,
        'type': 'log' if chart_mode == "log" else 'linear'
    }
    
    # 정규화 모드인 경우 y축 범위 설정
    if chart_mode == "percentage":
        yaxis_config['range'] = [0, 100]
    
    # x축 설정
    fig.update_layout(
        xaxis=dict(
            title="시간대",
            tickmode='array',
            tickvals=list(range(0, 24)),
            ticktext=[f"{h:02d}:00" for h in range(0, 24)]
        ),
        yaxis=yaxis_config,
        hovermode="x unified",
        template="plotly_white",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=80, b=20, l=20, r=20),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12
        )
    )
    
    # 로그 스케일 모드인 경우 안내 메시지 추가
    if chart_mode == "log":
        fig.update_layout(
            margin=dict(t=80, b=30, l=20, r=20)  # 하단 여백 적당히 설정
        )
    else:
        # 로그 스케일이 아닌 경우에도 여백 설정
        fig.update_layout(
            margin=dict(t=80, b=20, l=20, r=20)
        )
    
    return fig

# 페이지 레이아웃 정의
layout = create_management_layout() 