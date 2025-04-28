from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
from pages.region import create_region_layout, country_to_iso3
from pages.management import create_status_distribution_chart, load_bigquery_data
import plotly.graph_objects as go
import datetime
import pandas as pd
import plotly.express as px
import math
from dash import html
from dash.dependencies import Input, Output
from dash import dcc, html
from dash.html import Div

# 공통 상수 정의
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

def create_home_layout():
    # 공통 카드 스타일 정의
    card_style = {
        "backgroundColor": "white",
        "borderRadius": "10px",
        "padding": "20px",
        "height": "100%",
        "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.1)"
    }

    return html.Div([
        html.H2("대시보드"),
        html.Div([
            # 첫 번째 row - 3:9 비율 (유입 수와 지도)
            dbc.Row([
                # 왼쪽 3 - 최근 24시간 방문자 수
                dbc.Col([
                    dcc.Link(
                        html.Div([
                            html.H4("최근 24시간 방문자", className="text-center mb-4", style={"color": "#2c3e50"}),
                            html.Div([
                                html.H5("전체 방문자", className="text-center mb-1", style={"color": "#2c3e50"}),
                                html.H2(
                                    id='total-visitors-24h',
                                    className="text-center font-weight-bold mb-3",
                                    style={"color": "#6c757d", "fontSize": "2.5rem"}
                                ),
                                html.H5("신규 방문자", className="text-center mb-1", style={"color": "#2c3e50"}),
                                html.H2(
                                    id='new-visitors-24h',
                                    className="text-center font-weight-bold mb-3",
                                    style={"color": "#ff7f0e", "fontSize": "2.5rem"}
                                ),
                                html.H5("재방문자", className="text-center mb-1", style={"color": "#2c3e50"}),
                                html.H2(
                                    id='returning-visitors-24h',
                                    className="text-center font-weight-bold",
                                    style={"color": "#1f77b4", "fontSize": "2.5rem"}
                                )
                            ], style={
                                "height": "300px",
                                "display": "flex",
                                "flexDirection": "column",
                                "justifyContent": "center",
                                "gap": "0.5rem"
                            })
                        ], className="chart-container h-100 hover-effect", style=card_style),
                        href="/visitor-analysis",
                        style={"textDecoration": "none"}
                    )
                ], width=3),
                # 오른쪽 9 - 지도
                dbc.Col([
                    dcc.Link(
                        html.Div([
                            html.H4("지역별 접속 현황", style={"color": "#2c3e50"}),
                            dcc.Loading(
                                id="loading-region-map-home",
                                type="circle",
                                children=dcc.Graph(
                                    id='region-map-home',
                                    style={"height": "300px"}
                                )
                            )
                        ], className="chart-container h-100 hover-effect", style=card_style),
                        href="/region",
                        style={"textDecoration": "none"}
                    )
                ], width=9)
            ], className="mb-4"),

            # 두 번째 row - 트래픽 추이 (전체 너비)
            dbc.Row([
                dbc.Col([
                    dcc.Link(
                        html.Div([
                            html.H4("최근 24시간 트래픽 추이", style={"color": "#2c3e50"}),
                            dcc.Loading(
                                id="loading-traffic-chart",
                                type="circle",
                                children=dcc.Graph(
                                    id='traffic-chart',
                                    style={"height": "300px"}
                                )
                            )
                        ], className="chart-container h-100 hover-effect", style=card_style),
                        href="/traffic",
                        style={"textDecoration": "none"}
                    )
                ], width=12)
            ], className="mb-4"),

            # 세 번째 row - 6:6 비율
            dbc.Row([
                # 왼쪽 6 - 상태 코드 분포
                dbc.Col([
                    dcc.Link(
                        html.Div([
                            html.H4("상태 코드 분포", style={"color": "#2c3e50"}),
                            dcc.Loading(
                                id="loading-status-distribution-home",
                                type="circle",
                                children=dcc.Graph(
                                    id='status-distribution-home',
                                    style={"height": "300px"}
                                )
                            )
                        ], className="chart-container h-100 hover-effect", style=card_style),
                        href="/management",
                        style={"textDecoration": "none"}
                    )
                ], width=6),
                # 오른쪽 6 - 유입 URL 분포
                dbc.Col([
                    dcc.Link(
                        html.Div([
                            html.H4("유입 URL 분포", style={"color": "#2c3e50"}),
                            dcc.Loading(
                                id="loading-url-distribution-home",
                                type="circle",
                                children=dcc.Graph(
                                    id='url-distribution-home',
                                    style={"height": "300px"}
                                )
                            )
                        ], className="chart-container h-100 hover-effect", style=card_style),
                        href="/referrer",
                        style={"textDecoration": "none"}
                    )
                ], width=6)
            ])
        ], className="page-container")
    ])

@callback(
    Output('region-map-home', 'figure'),
    Input('region-map-home', 'id')
)
def update_region_map_home(_):
    # 최근 24시간의 지도 데이터 쿼리
    query = """
    WITH latest_time AS (
        SELECT TIMESTAMP(MAX(timestamp_utc)) as max_timestamp
        FROM `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
    ),
    time_range AS (
        SELECT 
            max_timestamp,
            TIMESTAMP_SUB(max_timestamp, INTERVAL 24 HOUR) as start_timestamp
        FROM latest_time
    ),
    base_data AS (
        SELECT 
            TRIM(SPLIT(REGEXP_REPLACE(geo, r'[[:space:]]*\\([^)]*\\)', ''), ',')[OFFSET(0)]) AS country,
            COUNT(*) as count
        FROM `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
        WHERE 
            geo IS NOT NULL 
            AND geo != '-' 
            AND geo != ''
            AND TIMESTAMP(timestamp_utc) >= (
                SELECT start_timestamp FROM time_range
            )
            AND TIMESTAMP(timestamp_utc) <= (
                SELECT max_timestamp FROM time_range
            )
        GROUP BY country
    )
    SELECT * FROM base_data
    ORDER BY count DESC
    """
    
    df = load_bigquery_data(query)
    
    if df.empty:
        return go.Figure()
    
    # ISO 코드 변환
    df['iso_alpha'] = df['country'].apply(lambda x: country_to_iso3(x))
    df = df.dropna(subset=['iso_alpha'])
    
    fig = px.choropleth(
        df,
        locations='iso_alpha',
        color='count',
        color_continuous_scale='deep',
        projection='natural earth',
        labels={'count': '접속 수'},
        title='국가별 웹서버 접근 수 (최근 24시간)'
    )

    fig.update_layout(
        autosize=True,
        height=300,
        margin=dict(l=0, r=0, t=40, b=0)
    )

    return fig

@callback(
    Output('status-distribution-home', 'figure'),
    Input('status-distribution-home', 'id')
)
def update_status_distribution_home(_):
    # 최근 24시간의 상태 코드 분포 데이터 쿼리
    query = """
    WITH latest_time AS (
        SELECT TIMESTAMP(MAX(timestamp_utc)) as max_timestamp
        FROM `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
    ),
    time_range AS (
        SELECT 
            max_timestamp,
            TIMESTAMP_SUB(max_timestamp, INTERVAL 24 HOUR) as start_timestamp
        FROM latest_time
    )
    SELECT
        status_code,
        FLOOR(status_code/100)*100 AS status_group,
        COUNT(*) as count
    FROM
        `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
    WHERE
        TIMESTAMP(timestamp_utc) >= (
            SELECT start_timestamp FROM time_range
        )
        AND TIMESTAMP(timestamp_utc) <= (
            SELECT max_timestamp FROM time_range
        )
    GROUP BY
        status_code, status_group
    """
    
    try:
        df = load_bigquery_data(query)
        if df is None or df.empty:
            return go.Figure()
        
        # 상태 코드 그룹별로 집계
        df['status_group_name'] = df['status_group'].apply(lambda x: f"{int(x//100)}xx")
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
        
        # 로그 스케일 적용
        log_values = [math.log10(max(1, val)) for val in group_df['count'].tolist()]
        min_val = min(log_values)
        if min_val < 1:
            log_values = [val - min_val + 1 for val in log_values]
        
        # 호버 텍스트 생성
        hover_texts = []
        for i, group in enumerate(labels):
            original_count = group_df.loc[group_df['status_group_name'] == group, 'count'].values[0]
            percentage = percentages[i]
            detail_text = f"<br><br>세부 상태 코드:<br>{status_details[group]}" if group in status_details else ""
            hover_texts.append(f"<b>{group}</b><br>총 건수: {original_count:,} ({percentage:.1f}%){detail_text}")
        
        colors = [COLOR_MAP.get(group, '#CCCCCC') for group in labels]
        
        # 파이 차트에 표시할 텍스트 생성
        text_template = '%{label}<br>%{text}%'
        text_values = [f"{p:.1f}" for p in percentages]
        
        # 파이 차트 추가
        fig.add_trace(go.Pie(
            labels=labels,
            values=log_values,
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
        
        fig.update_layout(
            title='상태 코드 분포 (최근 24시간, 로그 스케일)',
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
            height=300,
            margin=dict(t=80, b=30, l=20, r=20),
            hoverlabel=dict(
                bgcolor="white",
                font_size=12
            )
        )
        
        return fig
        
    except Exception as e:
        print(f"Error in update_status_distribution_home: {str(e)}")
        return go.Figure()

@callback(
    Output('traffic-chart', 'figure'),
    Input('traffic-chart', 'id')
)
def update_traffic_chart(_):
    query = """
    WITH latest_time AS (
        SELECT 
            TIMESTAMP_TRUNC(TIMESTAMP(MAX(timestamp_utc)), HOUR) as max_hour_timestamp
        FROM `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
    ),
    time_range AS (
        SELECT 
            max_hour_timestamp,
            TIMESTAMP_SUB(max_hour_timestamp, INTERVAL 23 HOUR) as start_timestamp
        FROM latest_time
    ),
    hourly_stats AS (
        SELECT
            TIMESTAMP_TRUNC(timestamp_utc, HOUR) as hour_timestamp,
            COUNT(*) as count
        FROM `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
        WHERE TIMESTAMP(timestamp_utc) >= (
            SELECT start_timestamp FROM time_range
        )
        AND TIMESTAMP(timestamp_utc) < (
            SELECT max_hour_timestamp FROM time_range
        )
        GROUP BY hour_timestamp
        ORDER BY hour_timestamp
    )
    SELECT 
        FORMAT_TIMESTAMP('%Y-%m-%d %H:00', hour_timestamp) as hour_label,
        count
    FROM hourly_stats
    """
    df = load_bigquery_data(query)
    if df.empty:
        return go.Figure()
    
    # 트래픽 바 차트 생성
    fig = px.bar(
        df,
        x='hour_label',
        y='count',
        labels={'hour_label': '시간', 'count': '트래픽 수'},
        color='count',  # 트래픽 수에 따른 색상 그라데이션
        color_continuous_scale='Viridis',  # 색상 스케일
        text='count'  # 바 위에 값 표시
    )

    # 레이아웃 업데이트
    fig.update_layout(
        autosize=True,
        height=300,
        margin=dict(l=0, r=0, t=40, b=0),
        plot_bgcolor='rgba(0,0,0,0)',  # 배경 투명
        paper_bgcolor='rgba(0,0,0,0)',  # 배경 투명
        title={
            'text': '최근 24시간 트래픽 추이',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20, color='#2c3e50')
        },
        xaxis=dict(
            title='시간',
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            zerolinecolor='rgba(128, 128, 128, 0.2)',
            tickfont=dict(size=12, color='#2c3e50'),
            tickangle=45  # x축 레이블 45도 회전
        ),
        yaxis=dict(
            title='트래픽 수',
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            zerolinecolor='rgba(128, 128, 128, 0.2)',
            tickfont=dict(size=12, color='#2c3e50')
        ),
        hovermode='x unified',  # 호버 모드 설정
        hoverlabel=dict(
            bgcolor='white',
            font_size=12,
            font_family='Arial'
        )
    )

    # 바 스타일링
    fig.update_traces(
        texttemplate='%{text:,}',  # 천 단위 구분자 추가
        textposition='outside',
        hovertemplate='시간: %{x}<br>트래픽: %{y:,}<extra></extra>',  # 호버 템플릿
        marker=dict(
            line=dict(
                width=1,
                color='rgba(0,0,0,0.2)'
            )
        )
    )

    return fig

@callback(
    [Output('total-visitors-24h', 'children'),
     Output('new-visitors-24h', 'children'),
     Output('returning-visitors-24h', 'children')],
    Input('total-visitors-24h', 'id')
)
def update_visitor_metrics_24h(_):
    """최근 24시간 방문자 수 메트릭을 업데이트합니다."""
    counts = load_visitor_counts_24h()
    
    if counts is None:
        return "0", "0", "0"
    
    return (
        f"{counts['total']:,}",
        f"{counts['new']:,}",
        f"{counts['returning']:,}"
    )

def load_visitor_counts_24h():
    """최근 24시간 내의 방문자 수를 계산합니다."""
    try:
        query = """
        WITH latest_time AS (
            SELECT TIMESTAMP(MAX(timestamp_utc)) as max_timestamp
            FROM `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
        ),
        first_visits AS (
            -- 전체 기간에서 각 IP와 User-agent의 첫 방문 시간
            SELECT 
                ip,
                user_agent,
                MIN(TIMESTAMP(timestamp_utc)) as first_visit_time
            FROM `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
            GROUP BY ip, user_agent
        ),
        period_visits AS (
            -- 최근 24시간 내의 각 IP와 User-agent의 마지막 방문 시간
            SELECT 
                ip,
                user_agent,
                MAX(TIMESTAMP(timestamp_utc)) as last_visit_time
            FROM `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
            WHERE TIMESTAMP(timestamp_utc) >= (
                SELECT TIMESTAMP_SUB(max_timestamp, INTERVAL 24 HOUR)
                FROM latest_time
            )
            GROUP BY ip, user_agent
        )
        SELECT 
            COUNT(*) as total_visitors,
            COUNTIF(p.last_visit_time = f.first_visit_time) as new_visitors,
            COUNTIF(p.last_visit_time != f.first_visit_time) as returning_visitors
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
        print(f"Error in load_visitor_counts_24h: {str(e)}")
        return None

def load_url_distribution_home():
    """최근 24시간 내 TOP 유입 페이지를 계산합니다."""
    try:
        query = """
        WITH latest_date AS (
            SELECT TIMESTAMP(MAX(timestamp_utc)) as max_timestamp
            FROM `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
        ),
        page_stats AS (
            SELECT 
                url_path,
                COUNT(*) as count
            FROM `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
            WHERE TIMESTAMP(timestamp_utc) >= (
                SELECT TIMESTAMP_SUB(max_timestamp, INTERVAL 24 HOUR)
                FROM latest_date
            )
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
        
        df = load_bigquery_data(query)
        
        if df is not None and not df.empty:
            return {
                'pages': df['url_path'].tolist(),
                'counts': df['count'].tolist()
            }
        return None
    except Exception as e:
        print(f"Error in load_url_distribution_home: {str(e)}")
        return None

@callback(
    Output('url-distribution-home', 'figure'),
    Input('url-distribution-home', 'id')
)
def update_url_distribution_home(_):
    """유입 페이지 분포 그래프를 업데이트합니다."""
    stats = load_url_distribution_home()
    
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
        title='유입 URL 분포 (최근 24시간)',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#2c3e50'),
        margin=dict(l=20, r=120, t=50, b=20),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.1,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1
        ),
        height=300
    )
    
    return fig

layout = create_home_layout() 