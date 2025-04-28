# 필요한 라이브러리 import
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Output, Input, callback, no_update
import pandas as pd
import plotly.express as px
import os
import pandas_gbq
from dotenv import load_dotenv
import plotly.graph_objects as go
import json
from utils.utils import load_bigquery_data, get_bigquery_config

# 환경변수 로드
load_dotenv()

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# BigQuery 설정
config = get_bigquery_config()
project_id = config['project_id']
dataset = config['dataset']
table = config['table']

# 색상 테마
COLOR_SCHEME = {
    'total': '#6c757d',     # 전체 방문자 - 회색
    'new': '#ff7f0e',       # 신규 방문자 - 주황
    'returning': '#1f77b4', # 재방문 방문자 - 파랑
    'background': '#f8f9fa',
    'text': '#2c3e50',
    'empty': '#e9ecef'
}

def get_date_range():
    """DB에서 날짜 범위를 조회합니다."""
    try:
        query = f"""
        SELECT 
            MIN(DATE(timestamp_utc)) as min_date,
            MAX(DATE(timestamp_utc)) as max_date
        FROM `{project_id}.{dataset}.{table}`
        """
        
        df = load_bigquery_data(query)
        
        if df is not None and not df.empty:
            return df['min_date'].iloc[0], df['max_date'].iloc[0]
        return None, None
    except Exception as e:
        return None, None

def create_visitor_analysis_layout():
    """방문자 분석 페이지 레이아웃을 생성합니다."""
    # DB에서 날짜 범위 조회
    min_date, max_date = get_date_range()
    
    if min_date is None or max_date is None:
        return None

    # 필터 컴포넌트
    filters = dbc.Card(
        dbc.CardBody([
            html.H4("필터", className="card-title"),
            dbc.Row([
                dbc.Col([
                    html.Label("기간 선택"),
                    dcc.DatePickerRange(
                        id='date-range',
                        start_date=min_date,
                        end_date=max_date,
                        display_format='YYYY-MM-DD'
                    )
                ], width=12),
            ])
        ]), className="mb-3"
    )

    # 주요 지표 카드
    metrics_cards = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("전체 방문자", className="text-center mb-0", style={"color": "#666"}),
                    html.H2(
                        id='total-visitors-metric',
                        className="text-center display-4 font-weight-bold mb-0",
                        style={"color": COLOR_SCHEME['total']}
                    )
                ])
            ], className="mb-3")
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("신규 방문자", className="text-center mb-0", style={"color": "#666"}),
                    html.H2(
                        id='new-visitors-metric',
                        className="text-center display-4 font-weight-bold mb-0",
                        style={"color": COLOR_SCHEME['new']}
                    )
                ])
            ], className="mb-3")
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("재방문 방문자", className="text-center mb-0", style={"color": "#666"}),
                    html.H2(
                        id='returning-visitors-metric',
                        className="text-center display-4 font-weight-bold mb-0",
                        style={"color": COLOR_SCHEME['returning']}
                    )
                ])
            ], className="mb-3"),
            html.Div(id='metrics-visibility-container')
        ], width=4),
    ])

    # 필터링된 방문자 수 패널
    filtered_visitors_panel = dbc.Card(
        dbc.CardBody([
            html.H5("필터링된 방문자 수", className="mb-2"),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H6("전체", className="text-center mb-0", style={"color": "#666"}),
                        html.H3(
                            id='filtered-total-visitors',
                            className="text-center font-weight-bold mb-0",
                            style={"color": COLOR_SCHEME['total']}
                        )
                    ])
                ], width=4),
                dbc.Col([
                    html.Div([
                        html.H6("모바일", className="text-center mb-0", style={"color": "#666"}),
                        html.H3(
                            id='filtered-mobile-visitors',
                            className="text-center font-weight-bold mb-0",
                            style={"color": COLOR_SCHEME['new']}
                        )
                    ])
                ], width=4),
                dbc.Col([
                    html.Div([
                        html.H6("데스크톱", className="text-center mb-0", style={"color": "#666"}),
                        html.H3(
                            id='filtered-desktop-visitors',
                            className="text-center font-weight-bold mb-0",
                            style={"color": COLOR_SCHEME['returning']}
                        )
                    ])
                ], width=4),
            ])
        ]), className="mb-3"
    )

    # 전체 레이아웃
    return html.Div([
        html.H2("방문자 분석", style={"textAlign": "center"}),
        filters,
        metrics_cards,
        filtered_visitors_panel,

        # dcc.Store 컴포넌트를 사용하여 데이터를 캐싱
        dcc.Store(id='visitor-data'),

        # 고정 섹션: 일별 방문자 수 그래프
        dbc.Card(
            dbc.CardBody([
                html.H4("일별 방문자 수", className="card-title"),
                dcc.Loading(
                    id="loading-daily-visitors",
                    type="circle",
                    children=dcc.Graph(id='daily-visitors-graph')
                )
            ]),
            className="mb-3"
        ),

        # 방문자 환경 분석 섹션
        dbc.Card(
            dbc.CardBody([
                html.H4("방문자 환경 분석", className="card-title"),
                # 기기 유형 필터를 환경 분석 카드 내부로 이동
                dbc.Row([
                    dbc.Col([
                        html.Label("기기 유형 필터"),
                        dcc.Dropdown(
                            id='device-filter',
                            options=[
                                {'label': '전체', 'value': 'all'},
                                {'label': '모바일', 'value': 'mobile'},
                                {'label': '데스크톱', 'value': 'desktop'}
                            ],
                            value='all',
                            className="mb-3"
                        )
                    ], width=12)
                ]),
                html.Div(id='environment-analysis-title', className="text-muted mb-3"),
                # 환경 분석 그래프들
                dbc.Row([
                    dbc.Col([
                        dcc.Loading(
                            id="loading-device-distribution",
                            type="circle",
                            children=dcc.Graph(id='device-distribution')
                        )
                    ], width=4),
                    dbc.Col([
                        dcc.Loading(
                            id="loading-browser-distribution",
                            type="circle",
                            children=dcc.Graph(id='browser-distribution')
                        )
                    ], width=4),
                    dbc.Col([
                        dcc.Loading(
                            id="loading-os-distribution",
                            type="circle",
                            children=dcc.Graph(id='os-distribution')
                        )
                    ], width=4),
                ])
            ]),
            className="mb-3"
        ),
    ])

def load_visitor_counts(start_date, end_date):
    """선택된 기간의 방문자 수를 계산합니다."""
    try:
        query = f"""
        WITH first_visits AS (
            -- 전체 기간에서 각 IP와 User-agent의 첫 방문일
            SELECT 
                ip,
                user_agent,
                MIN(DATE(timestamp_utc)) as first_visit_date
            FROM `{project_id}.{dataset}.{table}`
            GROUP BY ip, user_agent
        ),
        period_visits AS (
            -- 조회 기간에서 각 IP와 User-agent의 마지막 방문일
            SELECT 
                ip,
                user_agent,
                MAX(DATE(timestamp_utc)) as last_visit_date
            FROM `{project_id}.{dataset}.{table}`
            WHERE DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY ip, user_agent
        )
        SELECT 
            COUNT(*) as total_visitors,
            COUNTIF(p.last_visit_date = f.first_visit_date) as new_visitors,
            COUNTIF(p.last_visit_date != f.first_visit_date) as returning_visitors
        FROM period_visits p
        JOIN first_visits f ON p.ip = f.ip AND p.user_agent = f.user_agent
        """
        
        df = load_bigquery_data(query)
        
        if df is not None and not df.empty:
            return {
                'total': df['total_visitors'].iloc[0],
                'new': df['new_visitors'].iloc[0],
                'returning': df['returning_visitors'].iloc[0]
            }
        return None
    except Exception as e:
        return None

@callback(
    [Output('total-visitors-metric', 'children'),
     Output('new-visitors-metric', 'children'),
     Output('returning-visitors-metric', 'children')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_visitor_metrics(start_date, end_date):
    """방문자 수 메트릭을 업데이트합니다."""
    if not start_date or not end_date:
        return "0", "0", "0"
    
    counts = load_visitor_counts(start_date, end_date)
    
    if counts is None:
        return "0", "0", "0"
    
    return (
        f"{counts['total']:,}",
        f"{counts['new']:,}",
        f"{counts['returning']:,}"
    )

def load_filtered_visitor_counts(start_date, end_date):
    """선택된 기간의 필터링된 방문자 수를 계산합니다."""
    try:
        query = f"""
        WITH visitor_stats AS (
            SELECT 
                ip,
                user_agent,
                user_is_mobile
            FROM `{project_id}.{dataset}.{table}`
            WHERE DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY ip, user_agent, user_is_mobile
        )
        SELECT 
            COUNT(*) as total_visitors,
            COUNTIF(user_is_mobile) as mobile_visitors,
            COUNTIF(NOT user_is_mobile) as desktop_visitors
        FROM visitor_stats
        """
        
        df = load_bigquery_data(query)
        
        if df is not None and not df.empty:
            return {
                'total': df['total_visitors'].iloc[0],
                'mobile': df['mobile_visitors'].iloc[0],
                'desktop': df['desktop_visitors'].iloc[0]
            }
        return None
    except Exception as e:
        return None

@callback(
    [Output('filtered-total-visitors', 'children'),
     Output('filtered-mobile-visitors', 'children'),
     Output('filtered-desktop-visitors', 'children')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_filtered_visitors(start_date, end_date):
    """필터링된 방문자 수를 업데이트합니다."""
    if not start_date or not end_date:
        return "0", "0", "0"
    
    counts = load_filtered_visitor_counts(start_date, end_date)
    
    if counts is None:
        return "0", "0", "0"
    
    return (
        f"{counts['total']:,}",
        f"{counts['mobile']:,}",
        f"{counts['desktop']:,}"
    )

def load_daily_visitor_stats(start_date, end_date):
    """선택된 기간의 일별 방문자 통계를 계산합니다."""
    try:
        query = f"""
        WITH daily_visits AS (
            SELECT 
                DATE(timestamp_utc) as visit_date,
                ip,
                user_agent
            FROM `{project_id}.{dataset}.{table}`
            WHERE DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY visit_date, ip, user_agent
        )
        SELECT 
            visit_date,
            COUNT(*) as total_visitors,
            COUNTIF(visit_date = first_visit_date) as new_visitors,
            COUNTIF(visit_date != first_visit_date) as returning_visitors
        FROM (
            SELECT 
                d.*,
                MIN(visit_date) OVER (PARTITION BY ip, user_agent) as first_visit_date
            FROM daily_visits d
        )
        GROUP BY visit_date
        ORDER BY visit_date
        """
        
        df = load_bigquery_data(query)
        
        if df is not None and not df.empty:
            return {
                'dates': df['visit_date'].astype(str).tolist(),
                'total': df['total_visitors'].tolist(),
                'new': df['new_visitors'].tolist(),
                'returning': df['returning_visitors'].tolist()
            }
        return None
    except Exception as e:
        return None

@callback(
    Output('daily-visitors-graph', 'figure'),
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_daily_visitors_graph(start_date, end_date):
    """일별 방문자 수 그래프를 업데이트합니다."""
    if not start_date or not end_date:
        return go.Figure()
    
    stats = load_daily_visitor_stats(start_date, end_date)
    
    if stats is None:
        return go.Figure()
    
    fig = go.Figure()
    
    # 전체 방문자
    fig.add_trace(go.Bar(
        x=stats['dates'],
        y=stats['total'],
        name='전체 방문자',
        marker_color=COLOR_SCHEME['total']
    ))
    
    # 신규 방문자
    fig.add_trace(go.Bar(
        x=stats['dates'],
        y=stats['new'],
        name='신규 방문자',
        marker_color=COLOR_SCHEME['new']
    ))
    
    # 재방문자
    fig.add_trace(go.Bar(
        x=stats['dates'],
        y=stats['returning'],
        name='재방문자',
        marker_color=COLOR_SCHEME['returning']
    ))
    
    fig.update_layout(
        title='일별 방문자 수',
        xaxis_title='날짜',
        yaxis_title='방문자 수',
        template='plotly_white',
        hovermode='x unified',
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def load_environment_stats(start_date, end_date, device_type='all'):
    """선택된 기간의 방문자 환경 통계를 계산합니다."""
    try:
        # 기기 유형 필터 조건 추가
        device_filter = ""
        if device_type == 'mobile':
            device_filter = "AND user_is_mobile = TRUE"
        elif device_type == 'desktop':
            device_filter = "AND user_is_mobile = FALSE"

        query = f"""
        WITH visitor_stats AS (
            SELECT 
                ip,
                user_agent,
                user_is_mobile,
                user_browser,
                user_os
            FROM `{project_id}.{dataset}.{table}`
            WHERE DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
            {device_filter}
            GROUP BY ip, user_agent, user_is_mobile, user_browser, user_os
        )
        SELECT 
            COUNT(*) as total_visitors,
            COUNTIF(user_is_mobile) as mobile_visitors,
            COUNTIF(NOT user_is_mobile) as desktop_visitors,
            user_browser,
            user_os
        FROM visitor_stats
        GROUP BY user_browser, user_os
        """
        
        df = load_bigquery_data(query)
        
        if df is not None and not df.empty:
            # 기기 분포 계산
            device_stats = {
                'mobile': df['mobile_visitors'].sum(),
                'desktop': df['desktop_visitors'].sum()
            }
            
            # 브라우저 분포 계산
            browser_stats = df.groupby('user_browser')['total_visitors'].sum().to_dict()
            
            # OS 분포 계산
            os_stats = df.groupby('user_os')['total_visitors'].sum().to_dict()
            
            return {
                'device': device_stats,
                'browser': browser_stats,
                'os': os_stats
            }
        return None
    except Exception as e:
        return None

@callback(
    Output('device-distribution', 'figure'),
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('device-filter', 'value')]
)
def update_device_distribution(start_date, end_date, device_type):
    """기기 분포 그래프를 업데이트합니다."""
    if not start_date or not end_date:
        return go.Figure()
    
    stats = load_environment_stats(start_date, end_date, device_type)
    
    if stats is None:
        return go.Figure()
    
    device_stats = stats['device']
    total = device_stats['mobile'] + device_stats['desktop']
    
    fig = go.Figure(data=[go.Pie(
        labels=['모바일', '데스크톱'],
        values=[device_stats['mobile'], device_stats['desktop']],
        hole=0.3,
        marker_colors=[COLOR_SCHEME['new'], COLOR_SCHEME['returning']]
    )])
    
    fig.update_layout(
        title='기기 분포',
        template='plotly_white',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    
    return fig

@callback(
    Output('browser-distribution', 'figure'),
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('device-filter', 'value')]
)
def update_browser_distribution(start_date, end_date, device_type):
    """브라우저 분포 그래프를 업데이트합니다."""
    if not start_date or not end_date:
        return go.Figure()
    
    stats = load_environment_stats(start_date, end_date, device_type)
    
    if stats is None:
        return go.Figure()
    
    browser_stats = stats['browser']
    
    # 상위 5개 브라우저만 표시
    top_browsers = dict(sorted(browser_stats.items(), key=lambda x: x[1], reverse=True)[:5])
    
    fig = go.Figure(data=[go.Bar(
        x=list(top_browsers.keys()),
        y=list(top_browsers.values()),
        marker_color=COLOR_SCHEME['total']
    )])
    
    fig.update_layout(
        title='브라우저 분포',
        xaxis_title='브라우저',
        yaxis_title='방문자 수',
        template='plotly_white'
    )
    
    return fig

@callback(
    Output('os-distribution', 'figure'),
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('device-filter', 'value')]
)
def update_os_distribution(start_date, end_date, device_type):
    """OS 분포 그래프를 업데이트합니다."""
    if not start_date or not end_date:
        return go.Figure()
    
    stats = load_environment_stats(start_date, end_date, device_type)
    
    if stats is None:
        return go.Figure()
    
    os_stats = stats['os']
    
    # 상위 5개 OS만 표시
    top_os = dict(sorted(os_stats.items(), key=lambda x: x[1], reverse=True)[:5])
    
    fig = go.Figure(data=[go.Bar(
        x=list(top_os.keys()),
        y=list(top_os.values()),
        marker_color=COLOR_SCHEME['total']
    )])
    
    fig.update_layout(
        title='OS 분포',
        xaxis_title='운영체제',
        yaxis_title='방문자 수',
        template='plotly_white'
    )
    
    return fig

# 페이지 레이아웃 정의
layout = create_visitor_analysis_layout() 