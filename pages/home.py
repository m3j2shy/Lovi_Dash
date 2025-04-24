from dash import html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
from pages.region import create_region_layout, country_to_iso3
from pages.management import create_status_distribution_chart, load_bigquery_data
import plotly.graph_objects as go
import datetime
import pandas as pd
import plotly.express as px

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
            TRIM(SPLIT(REGEXP_REPLACE(geo, r'[[:space:]]*\([^)]*\)', ''), ',')[OFFSET(0)]) AS country,
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
        
        fig = create_status_distribution_chart(df, ['1xx', '2xx', '3xx', '4xx', '5xx'], 'normal')
        fig.update_layout(
            height=400,
            margin=dict(t=40, b=20, l=20, r=20),
            title='상태 코드 분포 (최근 24시간)'
        )
        return fig
        
    except Exception as e:
        print(f"Error in update_status_distribution_home: {str(e)}")
        return go.Figure()

layout = create_home_layout() 