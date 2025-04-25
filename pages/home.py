from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
from pages.region import create_region_layout, country_to_iso3
from pages.management import create_status_distribution_chart, load_bigquery_data
import plotly.graph_objects as go
import datetime
import pandas as pd
import plotly.express as px
import math

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
    return html.Div([
        html.H2("대시보드"),
        html.Div([
            html.Div([
                html.H4("최근 24시간 트래픽 추이"),
                dcc.Loading(
                    id="loading-traffic-chart",
                    type="circle",
                    children=dcc.Graph(id='traffic-chart')
                )
            ], className="chart-container"),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H4("지역별 접속 현황"),
                        dcc.Loading(
                            id="loading-region-map-home",
                            type="circle",
                            children=dcc.Graph(id='region-map-home')
                        )
                    ], className="chart-container")
                ], width=6),
                dbc.Col([
                    html.Div([
                        html.H4("상태 코드 분포"),
                        dcc.Loading(
                            id="loading-status-distribution-home",
                            type="circle",
                            children=dcc.Graph(id='status-distribution-home')
                        )
                    ], className="chart-container")
                ], width=6)
            ], className="mb-4"),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H4("인기 키워드"),
                        dcc.Loading(
                            id="loading-popular-keywords",
                            type="circle",
                            children=dcc.Graph(id='popular-keywords-chart')
                        )
                    ], className="chart-container")
                ], width=6),
                dbc.Col([
                    html.Div([
                        html.H4("지역 분포"),
                        dcc.Loading(
                            id="loading-region-distribution",
                            type="circle",
                            children=dcc.Graph(id='region-distribution-chart')
                        )
                    ], className="chart-container")
                ], width=6)
            ])
        ], className="page-container")
    ])

@callback(
    Output('region-map-home', 'figure'),
    Input('region-map-home', 'id')
)
def update_region_map_home(_):
    # 가장 최근 날짜의 지도 데이터 쿼리
    query = """
    WITH latest_date AS (
        SELECT DATE(MAX(timestamp_utc)) as max_date
        FROM `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
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
            AND DATE(timestamp_utc) = (SELECT max_date FROM latest_date)
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
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )

    return fig

@callback(
    Output('status-distribution-home', 'figure'),
    Input('status-distribution-home', 'id')
)
def update_status_distribution_home(_):
    # 가장 최근 날짜의 상태 코드 분포 데이터 쿼리
    query = """
    WITH latest_date AS (
        SELECT DATE(MAX(timestamp_utc)) as max_date
        FROM `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
    )
    SELECT
        status_code,
        FLOOR(status_code/100)*100 AS status_group,
        COUNT(*) as count
    FROM
        `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
    WHERE
        DATE(timestamp_utc) = (SELECT max_date FROM latest_date)
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
            height=400,
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
    WITH latest_date AS (
        SELECT DATE(MAX(timestamp_utc)) as max_date
        FROM `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
    )
    SELECT
        EXTRACT(HOUR FROM timestamp_utc) as hour_to_24,
        COUNT(*) as count
    FROM
        `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
    WHERE
        DATE(timestamp_utc) = (SELECT max_date FROM latest_date)
    GROUP BY
        hour_to_24
    ORDER BY
        hour_to_24
    """
    df = load_bigquery_data(query)
    if df.empty:
        return go.Figure()
    
    # 트래픽 바 차트 생성
    fig = px.bar(
        df,
        x='hour_to_24',
        y='count',
        title='최근 24시간 트래픽 추이',
        labels={'hour_to_24': '시간', 'count': '트래픽 수'},
        color='count',  # 트래픽 수에 따른 색상 그라데이션
        color_continuous_scale='Viridis',  # 색상 스케일
        text='count'  # 바 위에 값 표시
    )

    # 레이아웃 업데이트
    fig.update_layout(
        autosize=True,
        height=400,
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
            title='시간(24H)',
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            zerolinecolor='rgba(128, 128, 128, 0.2)',
            tickfont=dict(size=12, color='#2c3e50')
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

layout = create_home_layout() 