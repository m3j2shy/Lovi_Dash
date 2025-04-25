import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Output, Input, callback
import pandas as pd
import plotly.express as px
import os
from dotenv import load_dotenv
import plotly.graph_objects as go
import numpy as np
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
    'total': '#6c757d',      # 전체 - 회색
    'direct': '#ff7f0e',     # 직접 접속 - 주황색
    'social': '#1f77b4',     # 소셜 미디어 - 파란색
    'search': '#2ca02c',     # 검색 엔진 - 초록색
    'others': '#d62728',     # 기타 - 빨간색
    '직접 접속': '#ff7f0e',  # 직접 접속 - 주황색
    '소셜 미디어': '#1f77b4', # 소셜 미디어 - 파란색
    '검색 엔진': '#2ca02c',   # 검색 엔진 - 초록색
    '기타': '#d62728',       # 기타 - 빨간색
    'background': '#f8f9fa',  # 배경색
    'text': '#2c3e50'        # 텍스트 색상
}

#load_data
DEFAULT_LIMIT = 10000

# 로딩 컴포넌트
loading_component = dbc.Spinner(
    html.Div(id="loading-output"),
    color="primary",
    type="grow",
    fullscreen=True
)

# 에러 메시지 컴포넌트
error_alert = dbc.Alert(
    "데이터를 불러오는 중 오류가 발생했습니다. 다시 시도해주세요.",
    id="error-message",
    color="danger",
    dismissable=True,
    is_open=False
)

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

def load_referrer_data(start_date=None, end_date=None, limit=DEFAULT_LIMIT):
    """유입 경로 분석을 위한 데이터를 로드합니다.
    
    Args:
        start_date (str, optional): 시작 날짜 (YYYY-MM-DD 형식)
        end_date (str, optional): 종료 날짜 (YYYY-MM-DD 형식)
        limit (int, optional): 데이터 로드 제한 수
    """
    try:
        # 기본 쿼리
        base_query = f"""
        SELECT 
            timestamp_utc,
            referrer_domain,
            url
        FROM `{project_id}.{dataset}.{table}`
        """
        
        # 날짜 필터 조건 추가
        where_conditions = []
        if start_date:
            where_conditions.append(f"DATE(timestamp_utc) >= '{start_date}'")
        if end_date:
            where_conditions.append(f"DATE(timestamp_utc) <= '{end_date}'")
        
        if where_conditions:
            base_query += "\nWHERE " + " AND ".join(where_conditions)
        
        # 정렬 및 제한
        query = base_query + "\nORDER BY timestamp_utc DESC"
        
        # limit이 None이 아닐 때만 LIMIT 절 추가
        if limit is not None:
            query += f"\nLIMIT {limit}"
        
        # utils.py의 load_bigquery_data 함수 사용
        df = load_bigquery_data(query)
        
        if df is not None and not df.empty:
            # timestamp_utc를 datetime으로 변환
            if 'timestamp_utc' in df.columns:
                df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
        
        return df
    except Exception as e:
        print(f"데이터 로드 중 오류 발생: {str(e)}")
        return None

# 유입 채널 분류 정의
REFERRER_CHANNELS = {
    'social': [
        'facebook.com', 'instagram.com', 'twitter.com', 'linkedin.com',
        't.co', 'fb.com', 'lnkd.in', 'social.com'
    ],
    'search': [
        'google.com', 'naver.com', 'daum.net', 'bing.com',
        'yahoo.com', 'duckduckgo.com'
    ],
    'direct': ['direct', '(direct)', '', None, 'zanbil.ir', 'znbl.ir', 'www.zanbil.ir', 'www.znbl.ir'],
}

def classify_referrer(domain):
    """referrer_domain을 채널별로 분류"""
    if domain in REFERRER_CHANNELS['direct']:
        return '직접 접속'
    
    # 도메인에서 서브도메인 제거 (예: blog.example.com -> example.com)
    base_domain = '.'.join(domain.split('.')[-2:]) if domain and '.' in domain else domain
    
    for channel, domains in REFERRER_CHANNELS.items():
        if any(ref in base_domain for ref in domains):
            if channel == 'social':
                return '소셜 미디어'
            elif channel == 'search':
                return '검색 엔진'
    
    return '기타'

def analyze_referrer_data(df):
    """유입 경로 데이터를 분석하여 통계를 생성합니다."""
    if df is None:
        print("데이터가 없습니다.")
        return None

    # 필요한 컬럼 추출
    required_columns = ['timestamp_utc', 'referrer_domain', 'url']
    
    # 컬럼 존재 여부 확인
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"필수 컬럼 누락: {missing_columns}")
        return None

    # 데이터 복사 (원본 데이터 보호)
    referrer_df = df[required_columns].copy()
    
    # 채널 분류 추가
    referrer_df['channel'] = referrer_df['referrer_domain'].apply(classify_referrer)
    
    # 1. 일별 유입 수 계산 (채널별)
    daily_stats = referrer_df.groupby([referrer_df['timestamp_utc'].dt.date, 'channel']).size().unstack(fill_value=0)
    
    # 2. 도메인별 유입 수 계산 (TOP 10)
    domain_stats = referrer_df.groupby(['referrer_domain', 'channel']).size().reset_index(name='count')
    domain_stats = domain_stats.sort_values('count', ascending=False)
    domain_stats = domain_stats[domain_stats['referrer_domain'].notna()]  # None 값 제외
    top_domains = domain_stats.head(10)
    
    # 3. 채널별 유입 수 계산
    channel_stats = referrer_df['channel'].value_counts()
    
    # 4. URL별 유입 수 계산 (TOP 10)
    url_stats = referrer_df['url'].value_counts().head(10)

    return {
        'daily_stats': daily_stats,
        'domain_stats': top_domains,
        'channel_stats': channel_stats,
        'url_stats': url_stats,
        'date_range': {
            'start': referrer_df['timestamp_utc'].min().date(),
            'end': referrer_df['timestamp_utc'].max().date()
        }
    }

def filter_data(df, start_date=None, end_date=None, channel=None):
    """데이터 필터링 함수"""
    if df is None:
        return None
        
    filtered_df = df.copy()
    
    # 날짜 필터링
    if start_date:
        filtered_df = filtered_df[filtered_df['timestamp_utc'].dt.date >= pd.to_datetime(start_date).date()]
    if end_date:
        filtered_df = filtered_df[filtered_df['timestamp_utc'].dt.date <= pd.to_datetime(end_date).date()]
    
    # 채널 분류 추가
    filtered_df['channel'] = filtered_df['referrer_domain'].apply(classify_referrer)
    
    # 채널 필터링
    if channel and channel != 'all':
        filtered_df = filtered_df[filtered_df['channel'] == channel]
    
    return filtered_df

def load_referrer_counts(start_date, end_date, channel='all'):
    """선택된 기간과 채널의 유입 수를 계산합니다."""
    try:
        # 기본 쿼리
        base_query = f"""
        SELECT 
            COUNT(*) as total_count,
            COUNTIF(referrer_domain IS NULL OR referrer_domain = '') as direct_count,
            COUNTIF(referrer_domain LIKE '%facebook.com%' OR referrer_domain LIKE '%instagram.com%' OR referrer_domain LIKE '%twitter.com%' OR referrer_domain LIKE '%linkedin.com%') as social_count,
            COUNTIF(referrer_domain LIKE '%google.com%' OR referrer_domain LIKE '%naver.com%' OR referrer_domain LIKE '%daum.net%' OR referrer_domain LIKE '%bing.com%') as search_count
        FROM `{project_id}.{dataset}.{table}`
        WHERE DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
        """
        
        df = load_bigquery_data(base_query)
        
        if df is not None and not df.empty:
            if channel == 'all':
                return df['total_count'].iloc[0]
            elif channel == '직접 접속':
                return df['direct_count'].iloc[0]
            elif channel == '소셜 미디어':
                return df['social_count'].iloc[0]
            elif channel == '검색 엔진':
                return df['search_count'].iloc[0]
            else:  # 기타
                return df['total_count'].iloc[0] - (df['direct_count'].iloc[0] + df['social_count'].iloc[0] + df['search_count'].iloc[0])
        return 0
    except Exception as e:
        return 0

def create_referrer_layout():
    """유입 경로 분석 페이지 레이아웃을 생성합니다."""
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
                        min_date_allowed=min_date,
                        max_date_allowed=max_date,
                        display_format='YYYY-MM-DD'
                    )
                ], width=6),
                dbc.Col([
                    html.Label("유입 채널"),
                    dcc.Dropdown(
                        id='channel-filter',
                        options=[
                            {'label': '전체', 'value': 'all'},
                            {'label': '직접 접속', 'value': '직접 접속'},
                            {'label': '소셜 미디어', 'value': '소셜 미디어'},
                            {'label': '검색 엔진', 'value': '검색 엔진'},
                            {'label': '기타', 'value': '기타'}
                        ],
                        value='all',
                        clearable=False
                    )
                ], width=6),
            ])
        ]), 
        className="mb-3"
    )

    # 주요 지표 카드
    metrics_cards = dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("전체 유입 수", className="text-center mb-0", style={"color": COLOR_SCHEME['total']}),
                    html.H2(
                        id='total-referrers-metric',
                        className="text-center display-4 font-weight-bold mb-0",
                        style={"color": COLOR_SCHEME['total']}
                    ),
                ])
            ], className="mb-3")
        ], width=12),
    ])

    return dbc.Container([
        html.H1("유입 경로 분석 대시보드", className="my-4"),
        error_alert,
        loading_component,
        filters,
        metrics_cards,
        
        # 상단 섹션: 일별 유입 수 그래프
        dbc.Card(
            dbc.CardBody([
                html.H4("일별 유입 수", className="card-title"),
                dcc.Loading(
                    id="loading-daily-referrers",
                    type="circle",
                    children=dcc.Graph(id='daily-referrers-graph')
                )
            ]),
            className="mb-3"
        ),
        
        # 중간 섹션: TOP 10 유입 경로와 채널별 비율
        dbc.Row([
            # 좌측: TOP 10 유입 경로 (막대그래프)
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.H4("TOP 10 유입 경로", className="card-title"),
                        dcc.Loading(
                            id="loading-top-referrers",
                            type="circle",
                            children=dcc.Graph(id='top-referrers-graph')
                        )
                    ])
                )
            ], width=8),
            
            # 우측: 채널별 비율 (파이차트)
            dbc.Col([
                dbc.Card(
                    dbc.CardBody([
                        html.H4("유입 채널 분포", className="card-title"),
                        dcc.Loading(
                            id="loading-channel-distribution",
                            type="circle",
                            children=dcc.Graph(id='channel-distribution')
                        )
                    ])
                )
            ], width=4),
        ], className="mb-3"),
        
        # 하단 섹션: 유입 URL 분포
        dbc.Card(
            dbc.CardBody([
                html.H4("유입 URL 분포", className="card-title"),
                dcc.Loading(
                    id="loading-url-distribution",
                    type="circle",
                    children=dcc.Graph(id='url-distribution')
                )
            ]),
            className="mb-3"
        ),
    ], fluid=True)

@callback(
    Output('total-referrers-metric', 'children'),
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('channel-filter', 'value')]
)
def update_total_referrers(start_date, end_date, channel):
    """전체 유입 수를 업데이트합니다."""
    if not start_date or not end_date:
        return "0"
    
    count = load_referrer_counts(start_date, end_date, channel)
    return f"{count:,}"

def load_daily_referrer_stats(start_date, end_date, channel='all'):
    """선택된 기간의 일별 유입 통계를 계산합니다."""
    try:
        # 기본 쿼리
        base_query = f"""
        WITH daily_stats AS (
            SELECT 
                DATE(timestamp_utc) as visit_date,
                COUNT(*) as total_count,
                COUNTIF(referrer_domain IS NULL OR referrer_domain = '') as direct_count,
                COUNTIF(referrer_domain LIKE '%facebook.com%' OR referrer_domain LIKE '%instagram.com%' OR referrer_domain LIKE '%twitter.com%' OR referrer_domain LIKE '%linkedin.com%') as social_count,
                COUNTIF(referrer_domain LIKE '%google.com%' OR referrer_domain LIKE '%naver.com%' OR referrer_domain LIKE '%daum.net%' OR referrer_domain LIKE '%bing.com%') as search_count,
                COUNT(*) - (
                    COUNTIF(referrer_domain IS NULL OR referrer_domain = '') +
                    COUNTIF(referrer_domain LIKE '%facebook.com%' OR referrer_domain LIKE '%instagram.com%' OR referrer_domain LIKE '%twitter.com%' OR referrer_domain LIKE '%linkedin.com%') +
                    COUNTIF(referrer_domain LIKE '%google.com%' OR referrer_domain LIKE '%naver.com%' OR referrer_domain LIKE '%daum.net%' OR referrer_domain LIKE '%bing.com%')
                ) as others_count
            FROM `{project_id}.{dataset}.{table}`
            WHERE DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY visit_date
        )
        SELECT 
            visit_date,
            direct_count,
            social_count,
            search_count,
            others_count
        FROM daily_stats
        ORDER BY visit_date
        """
        
        df = load_bigquery_data(base_query)
        
        if df is not None and not df.empty:
            return {
                'dates': df['visit_date'].astype(str).tolist(),
                'direct': df['direct_count'].tolist(),
                'social': df['social_count'].tolist(),
                'search': df['search_count'].tolist(),
                'others': df['others_count'].tolist()
            }
        return None
    except Exception as e:
        return None

@callback(
    Output('daily-referrers-graph', 'figure'),
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('channel-filter', 'value')]
)
def update_daily_referrers_graph(start_date, end_date, channel):
    """일별 유입 수 그래프를 업데이트합니다."""
    if not start_date or not end_date:
        return go.Figure()
    
    stats = load_daily_referrer_stats(start_date, end_date, channel)
    
    if stats is None:
        return go.Figure()
    
    fig = go.Figure()
    
    if channel == 'all':
        # 모든 채널을 색상별로 표시
        fig.add_trace(go.Scatter(
            x=stats['dates'],
            y=stats['direct'],
            name='직접 접속',
            mode='lines+markers',
            line=dict(color=COLOR_SCHEME['직접 접속']),
            marker=dict(color=COLOR_SCHEME['직접 접속'])
        ))
        fig.add_trace(go.Scatter(
            x=stats['dates'],
            y=stats['social'],
            name='소셜 미디어',
            mode='lines+markers',
            line=dict(color=COLOR_SCHEME['소셜 미디어']),
            marker=dict(color=COLOR_SCHEME['소셜 미디어'])
        ))
        fig.add_trace(go.Scatter(
            x=stats['dates'],
            y=stats['search'],
            name='검색 엔진',
            mode='lines+markers',
            line=dict(color=COLOR_SCHEME['검색 엔진']),
            marker=dict(color=COLOR_SCHEME['검색 엔진'])
        ))
        fig.add_trace(go.Scatter(
            x=stats['dates'],
            y=stats['others'],
            name='기타',
            mode='lines+markers',
            line=dict(color=COLOR_SCHEME['기타']),
            marker=dict(color=COLOR_SCHEME['기타'])
        ))
    else:
        # 선택된 채널만 표시
        channel_data = {
            '직접 접속': stats['direct'],
            '소셜 미디어': stats['social'],
            '검색 엔진': stats['search'],
            '기타': stats['others']
        }
        fig.add_trace(go.Scatter(
            x=stats['dates'],
            y=channel_data[channel],
            name=channel,
            mode='lines+markers',
            line=dict(color=COLOR_SCHEME[channel]),
            marker=dict(color=COLOR_SCHEME[channel])
        ))
    
    fig.update_layout(
        title='일별 유입 수',
        xaxis_title='날짜',
        yaxis_title='유입 수',
        plot_bgcolor=COLOR_SCHEME['background'],
        paper_bgcolor=COLOR_SCHEME['background'],
        font=dict(color=COLOR_SCHEME['text']),
        margin=dict(l=50, r=50, t=50, b=50),
        hovermode='x unified',
        yaxis=dict(
            type='log',
            title='유입 수 (로그 스케일)',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)'
        )
    )
    
    return fig

def load_top_referrers(start_date, end_date, channel='all'):
    """선택된 기간의 TOP 유입 경로를 계산합니다."""
    try:
        # 기본 쿼리
        base_query = f"""
        WITH referrer_stats AS (
            SELECT 
                referrer_domain,
                COUNT(*) as count
            FROM `{project_id}.{dataset}.{table}`
            WHERE DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY referrer_domain
        )
        SELECT 
            referrer_domain,
            count
        FROM referrer_stats
        WHERE referrer_domain IS NOT NULL AND referrer_domain != ''
        ORDER BY count DESC
        LIMIT 10
        """
        
        df = load_bigquery_data(base_query)
        
        if df is not None and not df.empty:
            # 채널 분류 추가
            df['channel'] = df['referrer_domain'].apply(classify_referrer)
            
            # 채널 필터링
            if channel != 'all':
                df = df[df['channel'] == channel]
            
            return {
                'domains': df['referrer_domain'].tolist(),
                'counts': df['count'].tolist(),
                'channels': df['channel'].tolist()
            }
        return None
    except Exception as e:
        return None

@callback(
    Output('top-referrers-graph', 'figure'),
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('channel-filter', 'value')]
)
def update_top_referrers_graph(start_date, end_date, channel):
    """TOP 유입 경로 그래프를 업데이트합니다."""
    if not start_date or not end_date:
        return go.Figure()
    
    stats = load_top_referrers(start_date, end_date, channel)
    
    if stats is None:
        return go.Figure()
    
    fig = go.Figure()
    
    # 각 채널별로 데이터를 그룹화하여 표시
    for domain, count, domain_channel in zip(stats['domains'], stats['counts'], stats['channels']):
        fig.add_trace(go.Bar(
            y=[domain],  # y축에 도메인을 표시
            x=[count],   # x축에 카운트를 표시
            name=domain,
            marker_color=COLOR_SCHEME[domain_channel],
            showlegend=False,
            orientation='h'  # 가로 방향으로 설정
        ))
    
    fig.update_layout(
        title='TOP 10 유입 경로',
        yaxis_title='유입 경로',
        xaxis_title='유입 수',
        plot_bgcolor=COLOR_SCHEME['background'],
        paper_bgcolor=COLOR_SCHEME['background'],
        font=dict(color=COLOR_SCHEME['text']),
        margin=dict(l=50, r=50, t=50, b=50),
        hovermode='y unified',
        xaxis=dict(
            type='log',
            title='유입 수 (로그 스케일)',
            showgrid=True,
            gridcolor='rgba(0,0,0,0.1)'
        ),
        yaxis=dict(
            autorange='reversed'  # y축을 역순으로 정렬하여 가장 큰 값이 위에 오도록 함
        )
    )
    
    return fig

def load_channel_distribution(start_date, end_date):
    """선택된 기간의 채널별 유입 분포를 계산합니다."""
    try:
        # 기본 쿼리
        base_query = f"""
        WITH channel_stats AS (
            SELECT 
                CASE 
                    WHEN referrer_domain IS NULL OR referrer_domain = '' THEN '직접 접속'
                    WHEN referrer_domain LIKE '%facebook.com%' OR referrer_domain LIKE '%instagram.com%' OR referrer_domain LIKE '%twitter.com%' OR referrer_domain LIKE '%linkedin.com%' THEN '소셜 미디어'
                    WHEN referrer_domain LIKE '%google.com%' OR referrer_domain LIKE '%naver.com%' OR referrer_domain LIKE '%daum.net%' OR referrer_domain LIKE '%bing.com%' THEN '검색 엔진'
                    ELSE '기타'
                END as channel,
                COUNT(*) as count
            FROM `{project_id}.{dataset}.{table}`
            WHERE DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
            GROUP BY channel
        )
        SELECT 
            channel,
            count
        FROM channel_stats
        ORDER BY count DESC
        """
        
        df = load_bigquery_data(base_query)
        
        if df is not None and not df.empty:
            return {
                'channels': df['channel'].tolist(),
                'counts': df['count'].tolist()
            }
        return None
    except Exception as e:
        return None

@callback(
    Output('channel-distribution', 'figure'),
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_channel_distribution(start_date, end_date):
    """채널 분포 파이 차트를 업데이트합니다."""
    if not start_date or not end_date:
        return go.Figure()
    
    stats = load_channel_distribution(start_date, end_date)
    
    if stats is None:
        return go.Figure()
    
    # 실제 비율 계산
    total = sum(stats['counts'])
    percentages = [count / total * 100 for count in stats['counts']]
    
    fig = go.Figure()
    
    # 파이 차트 생성
    fig.add_trace(go.Pie(
        labels=stats['channels'],
        values=stats['counts'],  # 실제 값 사용
        marker=dict(colors=[COLOR_SCHEME[channel] for channel in stats['channels']]),
        textinfo='label+percent',
        insidetextorientation='radial',
        hole=0.3,
        hovertemplate="<b>%{label}</b><br>" +
                     "유입 수: %{value:,}<br>" +
                     "비율: %{percent:.1%}<extra></extra>"
    ))
    
    fig.update_layout(
        title='유입 채널 분포',
        plot_bgcolor=COLOR_SCHEME['background'],
        paper_bgcolor=COLOR_SCHEME['background'],
        font=dict(color=COLOR_SCHEME['text']),
        margin=dict(l=50, r=50, t=50, b=50),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def load_url_distribution(start_date, end_date, channel='all'):
    """선택된 기간의 TOP 유입 페이지를 계산합니다."""
    try:
        # 기본 쿼리
        base_query = f"""
        WITH page_stats AS (
            SELECT 
                url_path,
                COUNT(*) as count
            FROM `{project_id}.{dataset}.{table}`
            WHERE DATE(timestamp_utc) BETWEEN '{start_date}' AND '{end_date}'
            AND url_path IS NOT NULL 
            AND url_path != ''
            AND url_path != '/'
            GROUP BY url_path
        )
        SELECT 
            url_path,
            count
        FROM page_stats
        ORDER BY count DESC
        LIMIT 10
        """
        
        df = load_bigquery_data(base_query)
        
        if df is not None and not df.empty:
            return {
                'pages': df['url_path'].tolist(),
                'counts': df['count'].tolist()
            }
        return None
    except Exception as e:
        return None

@callback(
    Output('url-distribution', 'figure'),
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('channel-filter', 'value')]
)
def update_url_distribution(start_date, end_date, channel):
    """유입 페이지 분포 그래프를 업데이트합니다."""
    if not start_date or not end_date:
        return go.Figure()
    
    stats = load_url_distribution(start_date, end_date, channel)
    
    if stats is None:
        return go.Figure()
    
    fig = go.Figure()
    
    # 파이 차트 생성
    fig.add_trace(go.Pie(
        labels=stats['pages'],
        values=stats['counts'],
        textinfo='percent',  # 퍼센트만 표시
        textposition='auto',  # 자동 위치 조정
        hole=0.3,
        showlegend=True,  # 범례 표시
        hovertemplate="<b>%{label}</b><br>" +
                     "유입 수: %{value:,}<br>" +
                     "비율: %{percent:.1%}<extra></extra>"
    ))
    
    # 색상 팔레트 생성 (10개의 구분되는 색상)
    colors = [
        '#636EFA',  # 파란색
        '#EF553B',  # 빨간색
        '#00CC96',  # 초록색
        '#AB63FA',  # 보라색
        '#FFA15A',  # 주황색
        '#19D3F3',  # 하늘색
        '#FF6692',  # 분홍색
        '#B6E880',  # 연두색
        '#FF97FF',  # 자주색
        '#FECB52'   # 노란색
    ]
    
    fig.update_traces(marker=dict(colors=colors))
    
    fig.update_layout(
        title='유입 URL 분포',
        plot_bgcolor=COLOR_SCHEME['background'],
        paper_bgcolor=COLOR_SCHEME['background'],
        font=dict(color=COLOR_SCHEME['text']),
        margin=dict(l=20, r=300, t=50, b=20),  # 오른쪽 여백을 더 크게
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.1,
            bgcolor=COLOR_SCHEME['background'],
            bordercolor=COLOR_SCHEME['text'],
            borderwidth=1
        ),
        width=1200,  # 전체 차트 너비
        height=300   # 차트 높이를 300px로 감소
    )
    
    return fig

# 페이지 레이아웃 정의
layout = create_referrer_layout()

# 데이터 로드
df = load_referrer_data()
if df is not None:
    # 날짜 범위 설정
    min_date = df['timestamp_utc'].min().date()
    max_date = df['timestamp_utc'].max().date()
    
    # 날짜 범위로 데이터 필터링
    df = df[(df['timestamp_utc'].dt.date >= min_date) & (df['timestamp_utc'].dt.date <= max_date)]
    
    analysis_results = analyze_referrer_data(df)
else:
    analysis_results = None
    min_date = None
    max_date = None



    # if __name__ == "__main__":

    #     print("\n유입 경로 분석 데이터 로드 중...")
    #     referrer_df = load_referrer_data()
    #     if referrer_df is not None:
    #         print(f"\n유입 경로 분석 데이터 로드 완료: {len(referrer_df)}행")
    #         print(referrer_df.head()) 
        
