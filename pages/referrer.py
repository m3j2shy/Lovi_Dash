import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Output, Input, callback, no_update
import pandas as pd
import plotly.express as px
import os
import pandas_gbq
from dotenv import load_dotenv
import plotly.graph_objects as go
import numpy as np

# 환경변수 로드
load_dotenv()

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# BigQuery 설정
project_id = os.getenv('GCP_PROJECT_ID')
dataset = os.getenv('BIGQUERY_DATASET')
table = os.getenv('BIGQUERY_TABLE')

#load_data
DEFAULT_LIMIT = 10000


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
        
        # 데이터 로드
        df = pandas_gbq.read_gbq(query, project_id=project_id)
        
        # timestamp_utc를 datetime으로 변환
        if 'timestamp_utc' in df.columns:
            df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
        
        return df
    except Exception as e:
        print(f"데이터 로드 중 오류 발생: {str(e)}")
        return None



    #함수들
    
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

if __name__ == '__main__':
    print("데이터 로드 중...")
    df = load_referrer_data()
    
    if df is not None:
        print(f"\n분석 기간: {df['timestamp_utc'].min().date()} ~ {df['timestamp_utc'].max().date()}")
        analysis_results = analyze_referrer_data(df)
        
        if analysis_results:
            print("\n1. 일별 유입 수:")
            print(analysis_results['daily_stats'])
            
            print("\n2. 주요 유입 도메인:")
            print(analysis_results['domain_stats'])
            
            print("\n3. 주요 유입 채널:")
            print(analysis_results['channel_stats'])
            
            print("\n4. 주요 유입 URL:")
            print(analysis_results['url_stats']) 




#페이지 
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
                html.H4("전체 유입 수", className="text-center mb-0", style={"color": "#666"}),
                html.H2(
                    id='total-referrers-metric',
                    className="text-center display-4 font-weight-bold mb-0",
                    style={"color": COLOR_SCHEME['total']}
                ),
            ])
        ], className="mb-3")
    ], width=12),
])

# 전체 레이아웃
layout = dbc.Container([
    html.H1("유입 경로 분석 대시보드", className="my-4"),
    error_alert,
    loading_component,
    filters,
    metrics_cards,
    
    # 상단 섹션: 일별 유입 수 그래프
    dbc.Card(
        dbc.CardBody([
            html.H4("일별 유입 수", className="card-title"),
            dcc.Graph(id='daily-referrers-graph')
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
                    dcc.Graph(id='top-referrers-graph')
                ])
            )
        ], width=8),
        
        # 우측: 채널별 비율 (파이차트)
        dbc.Col([
            dbc.Card(
                dbc.CardBody([
                    html.H4("유입 채널 분포", className="card-title"),
                    dcc.Graph(id='channel-distribution')
                ])
            )
        ], width=4),
    ], className="mb-3"),
    
    # 하단 섹션: 유입 URL 분포
    dbc.Card(
        dbc.CardBody([
            html.H4("유입 URL 분포", className="card-title"),
            dcc.Graph(id='url-distribution')
        ]),
        className="mb-3"
    ),
], fluid=True)

# 콜백 함수들
@callback(
    [Output('daily-referrers-graph', 'figure'),
     Output('top-referrers-graph', 'figure'),
     Output('channel-distribution', 'figure'),
     Output('url-distribution', 'figure'),
     Output('total-referrers-metric', 'children'),
     Output('error-message', 'is_open')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date'),
     Input('channel-filter', 'value')]
)
def update_graphs(start_date, end_date, channel):
    print("\n=== update_graphs 콜백 실행 ===")
    print(f"시작 날짜: {start_date}")
    print(f"종료 날짜: {end_date}")
    print(f"선택된 채널: {channel}")
    
    try:
        if df is None or analysis_results is None:
            print("데이터가 없습니다")
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title_text="데이터가 없습니다",
                showlegend=False,
                height=300,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            return empty_fig, empty_fig, empty_fig, empty_fig, "0", False

        # 전체 유입 수는 필터링 없이 계산
        total_referrers = len(df)
        print(f"전체 유입 수: {total_referrers}")
        
        # 채널 필터링된 데이터로 다른 그래프 생성
        filtered_df = filter_data(df, start_date, end_date, channel)
        print(f"필터링 후 데이터: {len(filtered_df) if filtered_df is not None else 0}행")
        
        if filtered_df.empty:
            print("필터링된 데이터가 없습니다")
            empty_fig = go.Figure()
            empty_fig.update_layout(
                title_text="선택한 기간에 데이터가 없습니다",
                showlegend=False,
                height=300,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            return empty_fig, empty_fig, empty_fig, empty_fig, f"{total_referrers:,}", False

        analysis = analyze_referrer_data(filtered_df)
        print("분석 결과 생성 완료")
        
        # 디버깅 정보 출력
        print("\n=== 디버깅 정보 ===")
        print(f"선택된 채널: {channel}")
        print(f"필터링된 데이터 수: {len(filtered_df)}")
        print("\n일별 통계:")
        print(analysis['daily_stats'])
        print("\n채널별 통계:")
        print(analysis['channel_stats'])
        print("\n도메인별 통계:")
        print(analysis['domain_stats'])
        print("==================\n")
        
        # 1. 일별 유입 수 그래프 (채널별 라인 그래프)
        daily_fig = go.Figure()
        
        # 직접 접속을 제외한 채널들 먼저 표시
        non_direct_channels = [col for col in analysis['daily_stats'].columns if col != '직접 접속']
        for channel in non_direct_channels:
            daily_fig.add_trace(
                go.Scatter(
                    name=channel,
                    x=analysis['daily_stats'].index,
                    y=analysis['daily_stats'][channel],
                    mode='lines+markers',
                    line=dict(color=COLOR_SCHEME[channel], width=2),
                    marker=dict(size=8)
                )
            )
        
        # 직접 접속은 점선으로 표시
        if '직접 접속' in analysis['daily_stats'].columns:
            daily_fig.add_trace(
                go.Scatter(
                    name='직접 접속',
                    x=analysis['daily_stats'].index,
                    y=analysis['daily_stats']['직접 접속'],
                    mode='lines+markers',
                    line=dict(color=COLOR_SCHEME['직접 접속'], width=2, dash='dot'),
                    marker=dict(size=8)
                )
            )
        
        daily_fig.update_layout(
            title="일별 유입 수 (채널별)",
            height=400,
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
        print("일별 유입 수 그래프 생성 완료")
        
        # 2. TOP 10 유입 경로 막대그래프
        top_referrers = analysis['domain_stats']
        top_fig = go.Figure(
            data=[
                go.Bar(
                    x=top_referrers['count'],
                    y=top_referrers['referrer_domain'],
                    orientation='h',
                    marker_color=[COLOR_SCHEME[channel] for channel in top_referrers['channel']]
                )
            ]
        )
        top_fig.update_layout(
            title="TOP 10 유입 경로",
            height=400,
            yaxis={'categoryorder': 'total ascending'},
            plot_bgcolor=COLOR_SCHEME['background'],
            paper_bgcolor=COLOR_SCHEME['background'],
            font=dict(color=COLOR_SCHEME['text']),
            margin=dict(l=50, r=50, t=50, b=50),
            xaxis=dict(
                type='log',
                title='유입 수 (로그 스케일)',
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)'
            )
        )
        print("TOP 10 유입 경로 그래프 생성 완료")
        
        # 3. 채널별 비율 파이차트 (로그 스케일 적용)
        channel_stats = analysis['channel_stats']
        
        # 로그 스케일 적용을 위해 값 변환
        log_values = np.log1p(channel_stats.values)
        log_values = log_values / log_values.sum()  # 정규화
        
        channel_fig = px.pie(
            values=log_values,
            names=channel_stats.index,
            title="유입 채널 분포 (로그 스케일)",
            hole=0.3,
            color=channel_stats.index,
            color_discrete_map=COLOR_SCHEME
        )
        channel_fig.update_layout(
            height=400,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        print("채널별 비율 그래프 생성 완료")
        
        # 4. URL 분포 파이차트
        url_stats = analysis['url_stats']
        log_url_values = np.log1p(url_stats.values)
        log_url_values = log_url_values / log_url_values.sum()  # 정규화
        
        url_fig = px.pie(
            values=log_url_values,
            names=url_stats.index,
            title="유입 URL 분포 (로그 스케일)",
            hole=0.3
        )
        url_fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        print("URL 분포 그래프 생성 완료")
        
        return [
            daily_fig,
            top_fig,
            channel_fig,
            url_fig,
            f"{total_referrers:,}",
            False  # 에러 메시지 숨김
        ]
        
    except Exception as e:
        print(f"Error in update_graphs: {str(e)}")
        empty_fig = go.Figure()
        empty_fig.update_layout(
            title_text="오류가 발생했습니다",
            showlegend=False,
            height=300,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return empty_fig, empty_fig, empty_fig, empty_fig, "0", True  # 에러 메시지 표시



    # if __name__ == "__main__":

    #     print("\n유입 경로 분석 데이터 로드 중...")
    #     referrer_df = load_referrer_data()
    #     if referrer_df is not None:
    #         print(f"\n유입 경로 분석 데이터 로드 완료: {len(referrer_df)}행")
    #         print(referrer_df.head()) 
        
