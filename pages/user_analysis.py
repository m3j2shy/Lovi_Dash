# 필요한 라이브러리 import
import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Output, Input, callback, no_update
import pandas as pd
import plotly.express as px
import os
import pandas_gbq
from dotenv import load_dotenv
import plotly.graph_objects as go
import json  # 상단에 json import 추가

# 환경변수 로드
load_dotenv()

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# BigQuery 설정
project_id = os.getenv('GCP_PROJECT_ID')
dataset = os.getenv('BIGQUERY_DATASET')
table = os.getenv('BIGQUERY_TABLE')

# 로드 데이터
DEFAULT_LIMIT = 100000

# 색상 테마
COLOR_SCHEME = {
    'total': '#6c757d',     # 전체 사용자 - 회색
    'new': '#ff7f0e',       # 신규 사용자 - 주황
    'returning': '#1f77b4', # 재방문 사용자 - 파랑
    'background': '#f8f9fa',
    'text': '#2c3e50',
    'empty': '#e9ecef'
}

# 데이터 로드 함수
def load_data_for_user_analysis(limit=DEFAULT_LIMIT):
    """BigQuery에서 사용자 분석에 필요한 데이터를 로드합니다."""
    try:
        # 필요한 컬럼만 선택하여 쿼리
        base_query = f"""
        SELECT 
            timestamp_utc,
            ip,
            user_browser,
            user_os,
            user_is_mobile,
            user_is_bot,
            url
        FROM `{project_id}.{dataset}.{table}`
        ORDER BY timestamp_utc DESC
        """
        
        # limit이 None이 아닐 때만 LIMIT 절 추가
        query = base_query + (f"\nLIMIT {limit}" if limit is not None else "")
        
        # 데이터 로드
        df = pandas_gbq.read_gbq(query, project_id=project_id)
        
        # 데이터 전처리
        df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'])
        df['user_is_mobile'] = df['user_is_mobile'].astype(bool)
        df['user_is_bot'] = df['user_is_bot'].astype(bool)
        
        # 신규/재방문 사용자 식별 (IP 기준 첫 방문 시간으로 판단)
        df['first_visit'] = df.groupby('ip')['timestamp_utc'].transform('min')
        df['is_new_user'] = df['timestamp_utc'] == df['first_visit']
        
        return df
        
    except Exception as e:
        print(f"데이터 로드 중 오류 발생: {e}")
        return None

# 사용자 분석 함수
def analyze_user_data(df):
    """사용자 분석 관련 데이터 처리 및 필요한 컬럼 반환"""
    if df is None:
        print("데이터가 없습니다.")
        return None

    required_columns = ['timestamp_utc', 'ip', 'user_browser', 'user_os', 'user_is_mobile', 'user_is_bot', 'is_new_user']
    
    # 컬럼 존재 여부 확인
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"필수 컬럼 누락: {missing_columns}")
        return None

    # 데이터 복사 (원본 데이터 보호)
    user_df = df[required_columns].copy()
    
    # 1. 일별 사용자 수 계산
    daily_users = user_df.groupby(user_df['timestamp_utc'].dt.date).agg({
        'ip': 'nunique',  # 전체 사용자 수
    }).rename(columns={'ip': 'total_users'})
    
    # 신규 사용자 수 계산 (is_new_user가 True인 IP의 고유 개수)
    new_users = user_df[user_df['is_new_user'] == True].groupby(
        user_df[user_df['is_new_user'] == True]['timestamp_utc'].dt.date
    )['ip'].nunique()
    
    daily_users['new_users'] = new_users
    daily_users['new_users'] = daily_users['new_users'].fillna(0)  # NaN을 0으로 채움
    daily_users['returning_users'] = daily_users['total_users'] - daily_users['new_users']
    
    # DataFrame을 딕셔너리로 변환
    daily_users_dict = {
        'index': [str(date) for date in daily_users.index],
        'total_users': daily_users['total_users'].tolist(),
        'new_users': daily_users['new_users'].tolist(),
        'returning_users': daily_users['returning_users'].tolist()
    }
    
    # 2. 기기/브라우저/OS 분포
    device_stats = {
        'mobile_ratio': {str(k): v for k, v in user_df['user_is_mobile'].value_counts(normalize=True).to_dict().items()},
        'browser_ratio': {str(k): v for k, v in user_df['user_browser'].value_counts(normalize=True).head(5).to_dict().items()},
        'os_ratio': {str(k): v for k, v in user_df['user_os'].value_counts(normalize=True).head(5).to_dict().items()},
        'bot_ratio': {str(k): v for k, v in user_df['user_is_bot'].value_counts(normalize=True).to_dict().items()}
    }

    # 3. 신규/재방문 비율
    user_type_ratio = {str(k): v for k, v in user_df['is_new_user'].value_counts(normalize=True).to_dict().items()}

    return {
        'daily_stats': daily_users_dict,
        'device_stats': device_stats,
        'user_type_ratio': user_type_ratio,
        'total_unique_users': user_df['ip'].nunique(),
        'date_range': {
            'start': user_df['timestamp_utc'].min().date(),
            'end': user_df['timestamp_utc'].max().date()
        }
    }

# 데이터 필터링 함수
def filter_data(df, start_date=None, end_date=None, device_type=None, user_type=None):
    """데이터 필터링 함수"""
    if df is None:
        return None
        
    filtered_df = df.copy()
    
    # 날짜 필터링
    if start_date:
        filtered_df = filtered_df[filtered_df['timestamp_utc'].dt.date >= pd.to_datetime(start_date).date()]
    if end_date:
        filtered_df = filtered_df[filtered_df['timestamp_utc'].dt.date <= pd.to_datetime(end_date).date()]
    
    # 기기 유형 필터링
    if device_type and device_type != 'all':
        is_mobile = device_type == 'mobile'
        filtered_df = filtered_df[filtered_df['user_is_mobile'] == is_mobile]
    
    # 사용자 유형 필터링
    if user_type and user_type != 'all':
        if user_type == 'new':
            # 신규 사용자만 필터링
            filtered_df = filtered_df[filtered_df['is_new_user'] == True]
        elif user_type == 'returning':
            # 재방문 사용자만 필터링
            filtered_df = filtered_df[filtered_df['is_new_user'] == False]
    
    return filtered_df

# 데이터 로드 및 초기 날짜 범위 설정
df = load_data_for_user_analysis()
if df is not None:
    # 날짜 범위 설정
    min_date = df['timestamp_utc'].min().date()
    max_date = df['timestamp_utc'].max().date()
    
    # 날짜 범위로 데이터 필터링
    df = df[(df['timestamp_utc'].dt.date >= min_date) & (df['timestamp_utc'].dt.date <= max_date)]
    
    analysis_results = analyze_user_data(df)
else:
    analysis_results = None
    min_date = None
    max_date = None

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
            ], width=12),
        ])
    ]), className="mb-3"
)

# 주요 지표 카드
metrics_cards = dbc.Row([
    dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.H4("전체 사용자", className="text-center mb-0", style={"color": "#666"}),
                html.H2(
                    id='total-users-metric',
                    className="text-center display-4 font-weight-bold mb-0",
                    style={"color": COLOR_SCHEME['total']}
                ),
            ])
        ], className="mb-3")
    ], width=4),
    dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.H4("신규 사용자", className="text-center mb-0", style={"color": "#666"}),
                html.H2(
                    id='new-users-metric',
                    className="text-center display-4 font-weight-bold mb-0",
                    style={"color": COLOR_SCHEME['new']}
                ),
            ])
        ], className="mb-3")
    ], width=4),
    dbc.Col([
        dbc.Card([
            dbc.CardBody([
                html.H4("재방문 사용자", className="text-center mb-0", style={"color": "#666"}),
                html.H2(
                    id='returning-users-metric',
                    className="text-center display-4 font-weight-bold mb-0",
                    style={"color": COLOR_SCHEME['returning']}
                ),
            ])
        ], className="mb-3"),
        html.Div(id='metrics-visibility-container')
    ], width=4),
])

# 필터링된 사용자 수 패널
filtered_users_panel = dbc.Card(
    dbc.CardBody([
        html.H5("필터링된 사용자 수", className="mb-2"),
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H6("전체", className="text-center mb-0", style={"color": "#666"}),
                    html.H3(
                        id='filtered-total-users',
                        className="text-center font-weight-bold mb-0",
                        style={"color": COLOR_SCHEME['total']}
                    ),
                ])
            ], width=4),
            dbc.Col([
                html.Div([
                    html.H6("모바일", className="text-center mb-0", style={"color": "#666"}),
                    html.H3(
                        id='filtered-mobile-users',
                        className="text-center font-weight-bold mb-0",
                        style={"color": COLOR_SCHEME['new']}
                    ),
                ])
            ], width=4),
            dbc.Col([
                html.Div([
                    html.H6("데스크톱", className="text-center mb-0", style={"color": "#666"}),
                    html.H3(
                        id='filtered-desktop-users',
                        className="text-center font-weight-bold mb-0",
                        style={"color": COLOR_SCHEME['returning']}
                    ),
                ])
            ], width=4),
        ])
    ]), className="mb-3"
)

# 전체 레이아웃
layout = dbc.Container([
    html.H1("사용자 분석 대시보드", className="my-4"),
    filters,
    metrics_cards,
    filtered_users_panel,  # 필터링된 사용자 수 패널을 상단에 고정

    # dcc.Store 컴포넌트를 사용하여 데이터를 캐싱
    dcc.Store(id='user-data'),

    # 고정 섹션: 일별 사용자 수 그래프
    dbc.Card(
        dbc.CardBody([
            html.H4("일별 사용자 수", className="card-title"),
            dcc.Graph(id='daily-users-graph')
        ]),
        className="mb-3"
    ),

    # 사용자 환경 분석 섹션
    dbc.Card(
        dbc.CardBody([
            html.H4("사용자 환경 분석", className="card-title"),
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
                dbc.Col([dcc.Graph(id='device-distribution')], width=4),
                dbc.Col([dcc.Graph(id='browser-distribution')], width=4),
                dbc.Col([dcc.Graph(id='os-distribution')], width=4),
            ])
        ]),
        className="mb-3"
    ),
], fluid=True)

app.layout = layout

# 콜백 함수 등록
@callback(
    Output('user-data', 'data'),
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def load_data(start_date, end_date):
    print("\n=== load_data 콜백 실행 ===")
    print(f"시작 날짜: {start_date}")
    print(f"종료 날짜: {end_date}")
    
    try:
        # 데이터 로드
        df = load_data_for_user_analysis()
        print(f"데이터 로드 완료: {len(df) if df is not None else 0}행")

        # 날짜 범위로 데이터 필터링
        if df is not None and start_date and end_date:
            df = df[(df['timestamp_utc'].dt.date >= pd.to_datetime(start_date).date()) & 
                   (df['timestamp_utc'].dt.date <= pd.to_datetime(end_date).date())]
        
        # 분석 결과 생성
        analysis_results = analyze_user_data(df)
        print("분석 결과 생성 완료")
        
        # 날짜 객체를 문자열로 변환
        if analysis_results and 'date_range' in analysis_results:
            analysis_results['date_range']['start'] = analysis_results['date_range']['start'].isoformat()
            analysis_results['date_range']['end'] = analysis_results['date_range']['end'].isoformat()
        
        return json.dumps(analysis_results)
    except Exception as e:
        print(f"Error in load_data: {str(e)}")
        return None

# 콜백 함수: 일별 사용자 수 그래프 업데이트
@callback(
    Output('daily-users-graph', 'figure'),
    Input('user-data', 'data')
)
def update_daily_users_graph(data):
    print("\n=== update_daily_users_graph 콜백 실행 ===")
    try:
        if data is None:
            print("데이터가 없습니다")
            return go.Figure()
            
        analysis_results = json.loads(data)
        print("데이터 파싱 완료")
        
        daily_stats = analysis_results['daily_stats']
        print(f"일별 통계 데이터: {len(daily_stats['index'])}행")
        
        # 일별 사용자 수 그래프 생성
        fig = go.Figure()
        
        # 전체 사용자
        fig.add_trace(go.Scatter(
            x=daily_stats['index'],
            y=daily_stats['total_users'],
            name='전체 사용자',
            line=dict(color=COLOR_SCHEME['total'], width=2),
            mode='lines+markers'
        ))
        
        # 신규 사용자
        fig.add_trace(go.Scatter(
            x=daily_stats['index'],
            y=daily_stats['new_users'],
            name='신규 사용자',
            line=dict(color=COLOR_SCHEME['new'], width=2),
            mode='lines+markers'
        ))
        
        # 재방문 사용자
        fig.add_trace(go.Scatter(
            x=daily_stats['index'],
            y=daily_stats['returning_users'],
            name='재방문 사용자',
            line=dict(color=COLOR_SCHEME['returning'], width=2),
            mode='lines+markers'
        ))
        
        fig.update_layout(
            title='일별 사용자 수',
            xaxis_title='날짜',
            yaxis_title='사용자 수',
            template='plotly_white',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        print("그래프 생성 완료")
        return fig
    except Exception as e:
        print(f"Error in update_daily_users_graph: {str(e)}")
        return go.Figure()

# 콜백 함수: 기기 분포 그래프 업데이트
@callback(
    Output('device-distribution', 'figure'),
    Input('user-data', 'data')
)
def update_device_distribution(data):
    print("\n=== update_device_distribution 콜백 실행 ===")
    try:
        if data is None:
            print("데이터가 없습니다")
            return go.Figure()
            
        analysis_results = json.loads(data)
        print("데이터 파싱 완료")
        
        device_stats = analysis_results['device_stats']
        print(f"기기 통계: {device_stats}")
        
        # 기기 분포 그래프 생성 (모바일/데스크톱 비율)
        mobile_ratio = float(device_stats['mobile_ratio'].get('True', 0))
        desktop_ratio = float(device_stats['mobile_ratio'].get('False', 0))
        
        fig = go.Figure(data=[go.Pie(
            labels=['모바일', '데스크톱'],
            values=[mobile_ratio, desktop_ratio],
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
        print("그래프 생성 완료")
        return fig
    except Exception as e:
        print(f"Error in update_device_distribution: {str(e)}")
        return go.Figure()

# 콜백 함수: 브라우저 분포 그래프 업데이트
@callback(
    Output('browser-distribution', 'figure'),
    Input('user-data', 'data')
)
def update_browser_distribution(data):
    print("\n=== update_browser_distribution 콜백 실행 ===")
    try:
        if data is None:
            print("데이터가 없습니다")
            return go.Figure()
            
        analysis_results = json.loads(data)
        print("데이터 파싱 완료")
        
        browser_ratio = analysis_results['device_stats']['browser_ratio']
        print(f"브라우저 비율: {browser_ratio}")
        
        # 브라우저 분포 그래프 생성
        labels = list(browser_ratio.keys())
        values = list(browser_ratio.values())
        fig = px.bar(x=labels, y=values, title='브라우저 분포')
        fig.update_layout(template='plotly_white')
        print("그래프 생성 완료")
        return fig
    except Exception as e:
        print(f"Error in update_browser_distribution: {str(e)}")
        return go.Figure()

# 콜백 함수: OS 분포 그래프 업데이트
@callback(
    Output('os-distribution', 'figure'),
    [Input('user-data', 'data'),
     Input('device-filter', 'value')]
)
def update_os_distribution(data, device_type):
    print("\n=== update_os_distribution 콜백 실행 ===")
    try:
        if data is None:
            print("데이터가 없습니다")
            return go.Figure()
            
        analysis_results = json.loads(data)
        print("데이터 파싱 완료")
        
        os_ratio = analysis_results['device_stats']['os_ratio']
        print(f"OS 비율: {os_ratio}")
        
        # OS 분포 그래프 생성
        labels = list(os_ratio.keys())
        values = list(os_ratio.values())
        fig = px.bar(x=labels, y=values, title='OS 분포')
        fig.update_layout(template='plotly_white')
        print("그래프 생성 완료")
        return fig
    except Exception as e:
        print(f"Error in update_os_distribution: {str(e)}")
        return go.Figure()

# 콜백 함수: 주요 지표 업데이트
@callback(
    [Output('total-users-metric', 'children'),
     Output('new-users-metric', 'children'),
     Output('returning-users-metric', 'children')],
    Input('user-data', 'data')
)
def update_metrics(data):
    print("\n=== update_metrics 콜백 실행 ===")
    try:
        if data is None:
            print("데이터가 없습니다")
            return "0", "0", "0"
            
        analysis_results = json.loads(data)
        print("데이터 파싱 완료")
        
        total_unique_users = analysis_results['total_unique_users']
        user_type_ratio = analysis_results['user_type_ratio']
        print(f"총 사용자 수: {total_unique_users}")
        print(f"사용자 유형 비율: {user_type_ratio}")
        
        # 주요 지표 업데이트
        total_users = total_unique_users
        new_users = int(float(user_type_ratio.get('True', 0)) * total_users)
        returning_users = int(float(user_type_ratio.get('False', 0)) * total_users)
        
        print(f"계산된 지표 - 전체: {total_users}, 신규: {new_users}, 재방문: {returning_users}")
        return f"{int(total_users):,}", f"{int(new_users):,}", f"{int(returning_users):,}"
    except Exception as e:
        print(f"Error in update_metrics: {str(e)}")
        return "0", "0", "0"

# 콜백 함수: 필터링된 사용자 수 업데이트
@callback(
    [Output('filtered-total-users', 'children'),
     Output('filtered-mobile-users', 'children'),
     Output('filtered-desktop-users', 'children')],
    Input('user-data', 'data')
)
def update_filtered_users(data):
    print("\n=== update_filtered_users 콜백 실행 ===")
    try:
        if data is None:
            print("데이터가 없습니다")
            return "0", "0", "0"
            
        analysis_results = json.loads(data)
        print("데이터 파싱 완료")
        
        device_stats = analysis_results['device_stats']
        total_unique_users = analysis_results['total_unique_users']
        print(f"총 사용자 수: {total_unique_users}")
        print(f"기기 통계: {device_stats}")
        
        # 필터링된 사용자 수 업데이트
        mobile_ratio = float(device_stats['mobile_ratio'].get('True', 0))
        desktop_ratio = float(device_stats['mobile_ratio'].get('False', 0))
        
        mobile_users = int(mobile_ratio * total_unique_users)
        desktop_users = int(desktop_ratio * total_unique_users)
        
        print(f"계산된 사용자 수 - 전체: {total_unique_users}, 모바일: {mobile_users}, 데스크톱: {desktop_users}")
        return f"{int(total_unique_users):,}", f"{int(mobile_users):,}", f"{int(desktop_users):,}"
    except Exception as e:
        print(f"Error in update_filtered_users: {str(e)}")
        return "0", "0", "0"

if __name__ == '__main__':
    print("데이터 로드 중...")
    df = load_data_for_user_analysis()
    
    if df is not None:
        print(f"\n분석 기간: {df['timestamp_utc'].min().date()} ~ {df['timestamp_utc'].max().date()}")
        analysis_results = analyze_user_data(df)
        
        if analysis_results:
            print("\n1. 일별 사용자 통계:")
            print(analysis_results['daily_stats'])
            
            print("\n2. 기기 분포:")
            print("- 모바일/데스크톱 비율:")
            for device, ratio in analysis_results['device_stats']['mobile_ratio'].items():
                print(f"  {device}: {ratio:.2%}")
            
            print("\n- 주요 브라우저 비율:")
            for browser, ratio in analysis_results['device_stats']['browser_ratio'].items():
                print(f"  {browser}: {ratio:.2%}")
            
            print("\n- 주요 OS 비율:")
            for os, ratio in analysis_results['device_stats']['os_ratio'].items():
                print(f"  {os}: {ratio:.2%}")
            
            print("\n- 봇 비율:")
            for is_bot, ratio in analysis_results['device_stats']['bot_ratio'].items():
                print(f"  {'봇' if is_bot else '일반 사용자'}: {ratio:.2%}")
            
            print("\n3. 신규/재방문 비율:")
            for is_new, ratio in analysis_results['user_type_ratio'].items():
                print(f"  {'신규' if is_new else '재방문'}: {ratio:.2%}")
            
            print(f"\n총 고유 사용자 수: {analysis_results['total_unique_users']}명") 