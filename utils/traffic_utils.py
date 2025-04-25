from utils.utils import load_bigquery_data, get_bigquery_config
import datetime
import pandas as pd
import plotly.express as px
# from prophet import Prophet
# from prophet.plot import plot_plotly, plot_components_plotly

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
        fig = px.bar(
            result,
            x='day',
            y='traffic_sum',
            color='traffic_sum',  # 트래픽 수에 따른 색상 그라데이션
            color_continuous_scale='Viridis',  # 색상 스케일
            text='traffic_sum'  # 바 위에 값 표시
        )

        fig.update_traces(
            texttemplate='%{y:,.3s}',  # 천 단위 구분자 추가
            textposition='inside',
            hovertemplate='날짜: %{x}<br>트래픽: %{y:,}<extra></extra>',  # 호버 템플릿
            marker=dict(
                line=dict(
                    width=1,
                    color='rgba(0,0,0,0.2)'
                )
            )
        )

        fig.update_layout(
            autosize=True,
            height=400,
            margin=dict(l=0, r=0, t=40, b=0),
            plot_bgcolor='rgba(0,0,0,0)',  # 배경 투명
            paper_bgcolor='rgba(0,0,0,0)',  # 배경 투명
            title={
                'text': '날짜 별 트래픽 총합',
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

    elif mode == 'line':
        fig = px.line(
            result,
            x='day',
            y='traffic_sum',
            title='날짜 별 트래픽 총합',
            markers=True,
            color_discrete_sequence=['#3498db'],  # 파란색 계열
            line_shape='spline'  # 부드러운 곡선
        )

        # 레이아웃 업데이트
        fig.update_layout(
            height=HEIGHT,
            plot_bgcolor='rgba(0,0,0,0)',  # 배경 투명
            paper_bgcolor='rgba(0,0,0,0)',  # 배경 투명
            title={
                'text': '날짜별 트래픽 추이',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=20, color='#2c3e50')
            },
            xaxis=dict(
                title='날짜',
                showgrid=True,
                gridcolor='rgba(128, 128, 128, 0.2)',
                zerolinecolor='rgba(128, 128, 128, 0.2)',
                tickfont=dict(size=12, color='#2c3e50'),
                tickmode='linear',
                dtick=86400000  # 1일 간격
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

        # 라인 스타일링
        fig.update_traces(
            line=dict(
                width=3,
                color='#3498db'  # 파란색 계열
            ),
            marker=dict(
                size=8,
                color='#3498db',
                line=dict(
                    width=2,
                    color='white'
                )
            ),
            hovertemplate='날짜: %{x}<br>트래픽: %{y:,.3s}<extra></extra>',  # 호버 템플릿
            showlegend=False  # 범례 숨기기
        )
  
    return fig

def fig_traffic_per_hour(result, mode):
    if mode == 'bar':
        fig = px.bar(result,
            x='hour_to_24',
            y='traffic_sum',
            color='traffic_sum',
            color_continuous_scale='Viridis',
            text='traffic_sum')
        
        fig.update_traces(
            texttemplate='%{y:,.3s}',  # 천 단위 구분자 추가
            textposition='outside',
            hovertemplate='시간: %{x}<br>트래픽: %{y:,}<extra></extra>',  # 호버 템플릿
            marker=dict(
                line=dict(
                    width=1,
                    color='rgba(0,0,0,0.2)'
                )
            )
        )

        # 레이아웃 업데이트
        fig.update_layout(
            autosize=True,
            height=400,
            margin=dict(l=0, r=0, t=40, b=0),
            plot_bgcolor='rgba(0,0,0,0)',  # 배경 투명
            paper_bgcolor='rgba(0,0,0,0)',  # 배경 투명
            title={
                'text': '시간대 별 트래픽 총합',
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
    elif mode == 'line':
        fig = px.line(
            result,
            x='hour_to_24',
            y='traffic_sum',
            markers=True,
            color_discrete_sequence=['#3498db'],  # 파란색 계열
            line_shape='spline'  # 부드러운 곡선
        )

        # 레이아웃 업데이트
        fig.update_layout(
            height=HEIGHT,
            plot_bgcolor='rgba(0,0,0,0)',  # 배경 투명
            paper_bgcolor='rgba(0,0,0,0)',  # 배경 투명
            title={
                'text': '시간대별 트래픽 추이',
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
                tickfont=dict(size=12, color='#2c3e50'),
                tickmode='linear',
                dtick=1  # 1시간 간격
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
            ),
            showlegend=False  # 범례 숨기기
        )

        # 라인 스타일링
        fig.update_traces(
            line=dict(
                width=3,
                color='#3498db'  # 파란색 계열
            ),
            marker=dict(
                size=8,
                color='#3498db',
                line=dict(
                    width=2,
                    color='white'
                )
            ),
            hovertemplate='시간: %{x}시<br>트래픽: %{y:,.3s}<extra></extra>'  # 호버 템플릿
        )
    return fig

def fig_traffic_per_day_compare_users(traffic_per_day, unique_users_per_day):
    df = pd.merge(traffic_per_day, unique_users_per_day, on='day', how='left')
    
    # 그룹 바 차트 생성
    fig = px.bar(
        df,
        x='day',
        y=['traffic_sum', 'users'],
        barmode='group',
        labels={'traffic_sum': '트래픽', 'users': '사용자 수'},
        color_discrete_sequence=['#3498db', '#2ecc71'],  # 트래픽과 사용자 수에 대한 색상 지정
        title='일별 트래픽 및 사용자 수 추이'
    )

    # 레이아웃 업데이트
    fig.update_layout(
        height=HEIGHT,
        plot_bgcolor='rgba(0,0,0,0)',  # 배경 투명
        paper_bgcolor='rgba(0,0,0,0)',  # 배경 투명
        title={
            'text': '일별 트래픽 및 사용자 수 추이',
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20, color='#2c3e50')
        },
        xaxis=dict(
            title='날짜',
            showgrid=True,
            gridcolor='rgba(128, 128, 128, 0.2)',
            zerolinecolor='rgba(128, 128, 128, 0.2)',
            tickfont=dict(size=12, color='#2c3e50'),
            tickformat='%Y-%m-%d',
            tickmode='linear',
            dtick=86400000  # 1일을 밀리초로 표현
        ),
        yaxis=dict(
            title='수량',
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
        ),
        legend=dict(
            title='구분',
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1
        ),
        barmode='group',
        bargap=0.15,  # 그룹 간 간격
        bargroupgap=0.1  # 바 간 간격
    )

    # 바 스타일링
    fig.update_traces(
        texttemplate='%{y:,.3s}',  # 천 단위 구분자 추가
        textposition='outside',
        hovertemplate='날짜: %{x}<br>%{fullData.name}: %{y:,.3s}<extra></extra>',  # 호버 템플릿
        marker=dict(
            line=dict(
                width=1,
                color='rgba(0,0,0,0.2)'
            )
        )
    )
    return fig

def fig_traffic_avg_per_hour(result):
    # 라인 차트 생성
    fig = px.line(
        result,
        x='hour_to_24',
        y='avg_traffic',
        markers=True,
        title='시간대별 평균 트래픽',
        labels={'hour_to_24': '시간', 'avg_traffic': '평균 트래픽'},
        line_shape='spline',  # 부드러운 곡선
        color_discrete_sequence=['#3498db']  # 파란색 계열
    )

    # 레이아웃 업데이트
    fig.update_layout(
        height=HEIGHT,
        plot_bgcolor='rgba(0,0,0,0)',  # 배경 투명
        paper_bgcolor='rgba(0,0,0,0)',  # 배경 투명
        title={
            'text': '시간대별 평균 트래픽',
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
            tickfont=dict(size=12, color='#2c3e50'),
            tickmode='linear',
            dtick=1  # 1시간 간격
        ),
        yaxis=dict(
            title='평균 트래픽',
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

    # 라인 스타일링
    fig.update_traces(
        line=dict(
            width=3,
            color='#3498db'  # 파란색 계열
        ),
        marker=dict(
            size=8,
            color='#3498db',
            line=dict(
                width=2,
                color='white'
            )
        ),
        hovertemplate='시간: %{x}시<br>평균 트래픽: %{y:,.3s}<extra></extra>',  # 호버 템플릿
        textposition='top center'
    )
    
    return fig

# def fig_traffic_predict(min_date_str, max_date_str, predict_date=PREDICT_DATE):
#     df_prophet = load_bigquery_data(f"""
#         SELECT
#             hour, COUNT(*) as traffic
#         FROM
#             `dev-voice-457205-p8.lovi_dataset.lovi_datatable`
#         WHERE
#             day BETWEEN '{min_date_str}' AND '{max_date_str}'
#         GROUP BY
#             hour
#         ORDER BY
#             hour
#     """)
    
#     # 데이터 준비
#     # df_prophet['hour'].apply(lambda x: datetime.datetime.strptime(x, '%Y-%m-%dT%H'))
#     df_prophet['ds'] = pd.to_datetime(df_prophet['hour'], format='%Y-%m-%dT%H')
#     df_prophet['y'] = df_prophet['traffic'].astype('int64')
#     print(df_prophet[['ds', 'y']].copy().head(5))
#     # df_prophet = pd.DataFrame({'ds': df_prophet['ds'], 'y':df_prophet['y']})
#     df_prophet_copy = df_prophet[['ds', 'y']].copy()
#     df_prophet_copy = df_prophet_copy.sort_values('ds').reset_index(drop=True)
#     print(df_prophet_copy.head(5))

#     # model = Prophet(
#     #     daily_seasonality=True,
#     #     weekly_seasonality=False,  # 5일 데이터로 주간 패턴 학습 불가
#     #     changepoint_prior_scale=0.05,  # 급격한 변화 민감도 조절[1][8]
#     #     stan_backend= None
#     # )
#     # model.fit(df_prophet)
#     # future = model.make_future_dataframe(periods=predict_date, freq='h')
#     # forecast = model.predict(future)

#     # fig_forecast = plot_plotly(model, forecast)
#     # fig_forecast.update_layout(
#     #     xaxis_title=f'{min_date_str} ~ {max_date_str}',
#     #     yaxis_title='트래픽 예측값'
#     # )

#     model = NeuralProphet(
#         n_forecasts=48,
#         n_lags=24,  # 72시간 과거 데이터 활용
#         yearly_seasonality=False,
#         weekly_seasonality=False,
#         daily_seasonality=True,
#         d_hidden=32 # 뉴런 축소
#     )
#     model.fit(df_prophet_copy, freq='h')
#     future = model.make_future_dataframe(df_prophet, periods=48)
#     forecast = model.predict(future)

#     fig_forecast = model.plot(forecast)

#     # fig_forecast.show()

#     return fig_forecast