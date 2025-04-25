from utils.utils import load_bigquery_data, get_bigquery_config
import datetime
import pandas as pd
import plotly.express as px
from prophet import Prophet
from prophet.plot import plot_plotly, plot_components_plotly

# BigQuery에서 데이터 로드
project_id, dataset, table = get_bigquery_config()
PREDICT_DATE = 48

# 날짜 데이터 조회
def get_date_range():
    query_for_date =f"""
        SELECT DISTINCT
            DATE(timestamp_utc) as date
        FROM
            `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
        ORDER BY 
            date
    """
    result = load_bigquery_data(query_for_date)

    # 날짜 범위 계산
    min_date_str = '2019-01-01'  # 기본값
    max_date_str = datetime.date.today().strftime('%Y-%m-%d')  # 기본값

    if not result.empty:
        result['date'] = pd.to_datetime(result['date']).dt.date
        min_date = result['date'].min()
        max_date = result['date'].max()
        min_date_str = min_date.strftime('%Y-%m-%d')
        max_date_str = max_date.strftime('%Y-%m-%d')
    
    return min_date_str, max_date_str

# 필요 데이터 query
"""
일 별 트래픽 총합
"""
def get_traffic_per_day(min_date_str, max_date_str):
    result  = load_bigquery_data(f"""
        SELECT
            day, count(*) as traffic_sum
        FROM
            `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
        WHERE
            day BETWEEN '{min_date_str}' AND '{max_date_str}'
        GROUP BY
            day
        ORDER BY
            day
    """)

    return result

"""
시간대 별 트래픽 총합
"""
def get_traffic_per_hour(min_date_str, max_date_str):
    result = load_bigquery_data(f"""
        SELECT 
            EXTRACT(HOUR FROM timestamp_utc) as hour_to_24, COUNT(*) as traffic_sum
        FROM 
            `dev-voice-457205-p8.lovi_dataset.lovi_datatable` 
        WHERE 
            day between '{min_date_str}' and '{max_date_str}'
        GROUP BY
            hour_to_24
        ORDER BY
            hour_to_24
    """)
    return result

"""
시간대 별 트래픽 평균
"""
def get_traffic_avg_per_hour(min_date_str, max_date_str):
    result = load_bigquery_data(f"""
        SELECT hour_to_24, CAST(AVG(traffic_sum) AS INT64) AS avg_traffic
        from (
            SELECT 
                day, EXTRACT(HOUR FROM timestamp_utc) as hour_to_24, COUNT(*) as traffic_sum
            FROM 
                `dev-voice-457205-p8.lovi_dataset.lovi_datatable` 
            WHERE 
                day between '{min_date_str}' and '{max_date_str}'
            GROUP BY
                day, hour_to_24
            ORDER BY
                day, hour_to_24
        )
        group by hour_to_24
        order by hour_to_24
    """
    )
    return result

# 일 별 고유 사용자 수 조회
def get_unique_users_per_day(min_date_str, max_date_str):
    result = load_bigquery_data(f"""
        SELECT
            day,
            COUNT(DISTINCT ip) as users
        FROM
            `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
        WHERE
            day BETWEEN '{min_date_str}' AND '{max_date_str}'
        GROUP BY
            day
        ORDER BY
            day
    """)
    return result

# FIG
HEIGHT = 450
def fig_traffic_per_day(result, mode):
    if mode == 'bar':
        fig = px.bar(result, x='day', y='traffic_sum', title='날짜 별 트래픽 총합')
        fig.update_traces(texttemplate='%{y:.3s}', textposition='inside')
    elif mode == 'line':
        fig = px.line(result, x='day', y='traffic_sum', title='날짜 별 트래픽 총합', markers=True)
    fig.update_layout(
        height=HEIGHT,
        xaxis_title='날짜',
        yaxis_title='트래픽 총합',
        xaxis_tickformat='%Y-%m-%d',
        xaxis_tickmode='linear',
        xaxis_dtick=86400000  # 1일을 밀리초로 표현
    )
        
    return fig

def fig_traffic_per_hour(result, mode):
    if mode == 'bar':
        fig = px.bar(result, x='hour_to_24', y='traffic_sum', title='시간대 별 트래픽 총합')
        fig.update_traces(texttemplate='%{y:.3s}', textposition='outside')
    elif mode == 'line':
        fig = px.line(result, x='hour_to_24', y='traffic_sum', title='시간대 별 트래픽 총합', markers=True)
    fig.update_layout(
        height=HEIGHT,
        xaxis_title='시간(24H)',
        yaxis_title='트래픽 총합',
    )
    return fig

def fig_traffic_per_day_compare_users(traffic_per_day, unique_users_per_day):
    df = pd.merge(traffic_per_day, unique_users_per_day, on='day', how='left')
    fig = px.bar(df, x='day', y=['traffic_sum', 'users'], barmode='group', labels={'traffic_sum': '트래픽', 'users': '사용자 수'})
    fig.update_layout(
        height=HEIGHT,
        xaxis_title='날짜',
        yaxis_title='트래픽',
        xaxis_tickformat='%Y-%m-%d',
        xaxis_tickmode='linear',
        xaxis_dtick=86400000  # 1일을 밀리초로 표현
    )
    fig.update_traces(texttemplate='%{y:.3s}', textposition='outside')
    return fig

def fig_traffic_avg_per_hour(result):
    fig = px.line(result, x='hour_to_24', y='avg_traffic', markers=True)

    fig.update_layout(
        height=HEIGHT,
        xaxis_title='시간(24H)',
        yaxis_title='트래픽 평균',
    )
    return fig

def fig_traffic_predict(min_date_str, max_date_str, predict_date=PREDICT_DATE):
    df_prophet = load_bigquery_data(f"""
        SELECT
            hour, COUNT(*) as traffic
        FROM
            `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
        WHERE
            day BETWEEN '{min_date_str}' AND '{max_date_str}'
        GROUP BY
            hour
        ORDER BY
            hour
    """)
    
    # 데이터 준비
    df_prophet = pd.DataFrame({'ds': df_prophet['hour'], 'y':df_prophet['traffic']})

    model = Prophet(
        daily_seasonality=True,
        weekly_seasonality=False,  # 5일 데이터로 주간 패턴 학습 불가
        changepoint_prior_scale=0.05  # 급격한 변화 민감도 조절[1][8]
    )
    model.fit(df_prophet)
    future = model.make_future_dataframe(periods=predict_date, freq='h')
    forecast = model.predict(future)

    fig_forecast = plot_plotly(model, forecast)
    fig_forecast.update_layout(
        xaxis_title=f'{min_date_str} ~ {max_date_str}',
        yaxis_title='트래픽 예측값'
    )

    return fig_forecast