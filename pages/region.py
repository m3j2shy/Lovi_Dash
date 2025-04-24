import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Output, Input, callback, no_update
import pandas as pd
import plotly.express as px
import os
import pandas_gbq
from dotenv import load_dotenv
import pycountry
import pycountry_convert as pc
import plotly.graph_objects as go

# 환경변수 로드
load_dotenv()

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # Gunicorn이 이 서버 객체를 사용합니다

# BigQuery에서 데이터 로드
project_id = os.getenv('GCP_PROJECT_ID')
dataset = os.getenv('BIGQUERY_DATASET')
table = os.getenv('BIGQUERY_TABLE')

def get_continent(country_name):
    try:
        if country_name == '-' or country_name.strip() == '':
            return None
        country_code = pc.country_name_to_country_alpha2(country_name, cn_name_format="default")
        continent_code = pc.country_alpha2_to_continent_code(country_code)
        continent_name = pc.convert_continent_code_to_continent_name(continent_code)
        return continent_name
    except:
        return None

def country_to_iso3(country_name):
    try:
        return pycountry.countries.lookup(country_name).alpha_3
    except LookupError:
        return None

# [1] 전역변수
# 전체 query 사용시 limit 추가 필수
# 일반적인 경우 where 조건 추가하여 호출
# (어차피 데이터 양이 많아서 전체 데이터 조회 시 쿼리 중간에 터짐)

# 국가(이름 구체), 도시 형태로 되어있어 국가이름만 추출하는 sql쿼리
query = f"""
WITH base_data AS (
  SELECT 
    TRIM(SPLIT(REGEXP_REPLACE(geo, r'\s*\([^)]*\)', ''), ',')[OFFSET(0)]) AS country,
    TRIM(SPLIT(REGEXP_REPLACE(geo, r'\s*\([^)]*\)', ''), ',')[OFFSET(1)]) AS city,
    day,
    user_is_bot
  FROM `{project_id}.{dataset}.{table}`
  WHERE geo IS NOT NULL  -- NULL 값 제외
    AND geo != '-'
    AND geo != ''              -- 빈 문자열 제외
  --LIMIT 1000 --테스트 시 limit해주기
),

aggregated_data AS (
  SELECT 
    country,
    city,
    day,
    user_is_bot,
    COUNT(*) as count
  FROM base_data
  GROUP BY country, city, day, user_is_bot
)

SELECT *
FROM aggregated_data
ORDER BY count DESC
"""

df = pandas_gbq.read_gbq(query, project_id=project_id)
df['iso_alpha'] = df['country'].apply(country_to_iso3)
df['continent'] = df['country'].apply(get_continent)
df = df.dropna(subset=['iso_alpha'])

# 날짜 범위 추출
start_date = df['day'].min()
end_date = df['day'].max()

# 국가별 빈도 집계
country_counts = df.groupby(['iso_alpha', 'country'])['count'].sum().reset_index()

# 도시별 빈도 집계
city_counts = df.groupby('city')['count'].sum().reset_index()

# 대륙별 빈도 집계
continent_counts = df.groupby(['iso_alpha', 'continent', 'country'])['count'].sum().reset_index()

# 3. 도시별 위도/경도 데이터 불러오기
# 예시: simplemaps worldcities.csv 사용
cities_db = pd.read_csv('./assets/worldcities.csv')  # columns: city, country, lat, lng, etc.

# print(df.head(20))

# [2] 레이아웃
def create_region_layout():
    return html.Div([
        html.H2("지역 분석"),
        html.Div([
            html.Div([
                # 필터 요소들
                dbc.Row([
                    dbc.Col([
                        html.H6("날짜 범위", style={'margin-bottom': '10px', 'font-weight': 'bold', 'color': '#333'}),
                        dcc.DatePickerRange(
                            id='region-date-picker',
                            start_date=start_date,
                            end_date=end_date
                        )
                    ], width=4),
                    dbc.Col([
                        html.H6("사용자 유형", style={'margin-bottom': '10px', 'font-weight': 'bold', 'color': '#333'}),
                        dcc.Checklist(
                            id='user-type-selector',
                            options=[
                                {'label': '봇', 'value': True},
                                {'label': '일반 사용자', 'value': False}
                            ],
                            value=[True, False],
                            inline=True,
                            style={'display': 'flex', 'gap': '20px'}
                        )
                    ], width=4),
                    dbc.Col([
                        html.H6("지역 단위", style={'margin-bottom': '10px', 'font-weight': 'bold', 'color': '#333'}),
                        dcc.Dropdown(
                            id='region-level-selector',
                            options=[
                                {'label': '국가', 'value': 'country'},
                                {'label': '대륙', 'value': 'continent'},
                                {'label': '도시', 'value': 'city'}
                            ],
                            value='country'
                        )
                    ], width=4)
                ], className="mb-4")
            ], className="filter-container"),
            
            html.Div([
                # 메인 차트
                dcc.Loading(
                    id="loading-region-map",
                    type="circle",
                    children=dcc.Graph(id='region-map-chart')
                )
            ], className="main-container")])
    ])

layout = create_region_layout()


# [3] callback함수
# 1) 선택지에 따라 이에 대한 figure 도출
@callback(Output('region-map-chart', 'figure'), 
          Input('region-level-selector', 'value'),
          Input('region-date-picker', 'start_date'),
          Input('region-date-picker', 'end_date'),
          Input('user-type-selector', 'value'))
def figure_update(value, start_date, end_date, user_types):
    # 날짜와 사용자 유형에 따라 데이터 필터링
    map_filtered_df = df[
        (df['day'].astype(str) >= start_date) & 
        (df['day'].astype(str) <= end_date) &
        (df['user_is_bot'].isin(user_types))
    ]
    
    if value == 'country':
        # 국가별 빈도 집계 (필터링된 데이터로)
        country_counts = map_filtered_df.groupby(['iso_alpha', 'country'])['count'].sum().reset_index()
        
        fig = px.choropleth(
            country_counts,
            locations='iso_alpha',
            color='count',
            color_continuous_scale='deep',
            projection='natural earth',
            labels={'count': '접속 수'},
            title='국가별 웹서버 접근 수',
            hover_name='country' 
        )

        fig.update_layout(
            autosize=True,
            width=1400,
            height=800,
            margin=dict(l=0, r=0, t=40, b=0),
            title={
                'text': '국가별 웹서버 접근 수',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {
                    'size': 24,
                    'color': 'black',
                    'family': 'Arial'
                }
            }
        )

        fig.update_geos(
            fitbounds="locations",
            showland=True,
            landcolor="White"
        )
        return fig

   
    elif value == 'continent':
        # 대륙별 접속 수 계산 (필터링된 데이터로)
        continent_counts = map_filtered_df.groupby(['iso_alpha', 'continent', 'country'])['count'].sum().reset_index()
        
        # 대륙별 색상 매핑
        continent_colors = {
            'Asia': 'Reds',
            'Europe': 'Blues',
            'Africa': 'Greens',
            'North America': 'Purples',
            'South America': 'Oranges',
            'Oceania': 'Greys'
        }
        
        # 각 대륙별로 다른 색상 스케일을 적용
        fig = go.Figure()
        
        for continent in continent_counts['continent'].unique():
            continent_data = continent_counts[continent_counts['continent'] == continent]
            color_scale = continent_colors.get(continent, 'Viridis')
            
            fig.add_trace(go.Choropleth(
                locations=continent_data['iso_alpha'],
                z=continent_data['count'],
                text=continent_data['country'],
                colorscale=color_scale,
                showscale=False,  # color scale 제거
                name=continent,
                hoverinfo='text+z',
                hovertemplate="<b>%{text}</b><br>" +
                             "대륙: " + continent + "<br>" +
                             "접속 수: %{z}<br>" +
                             "<extra></extra>"
            ))
        
        fig.update_layout(
            autosize=True,
            width=1400,
            height=800,
            margin=dict(l=0, r=0, t=40, b=0),
            title={
                'text': '대륙별 웹서버 접속 수',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {
                    'size': 24,
                    'color': 'black',
                    'family': 'Arial'
                }
            },
            geo=dict(
                projection_type='natural earth',
                fitbounds="locations",
                showland=True,
                landcolor="White"
            )
        )
        
        return fig
    elif value == 'city':
        # 도시별 빈도 집계 (필터링된 데이터로)
        city_counts = map_filtered_df.groupby('city')['count'].sum().reset_index()
        
        # 도시명 기준 병합 (필요시 국가명도 활용)
        merged = pd.merge(city_counts, cities_db, on='city', how='left')
        merged['scaled_count'] = merged['count'] * 1.5  # 스케일링 팩터 조절

        fig = px.scatter_geo(
            merged,
            lat='lat',
            lon='lng',
            size='scaled_count',  # 스케일링된 값 사용
            hover_name='city',
            hover_data={'count': True, 'scaled_count': False},  # scaled_count는 호버에서 숨김
            color='count',
            color_continuous_scale='Plasma',  # 색상 팔레트를 Plasma로 변경
            projection='natural earth',
            size_max=50,  # 버블 최대 크기 증가 (기본값: 20)
            title='도시별 웹서버 접근 수'
        )
        fig.update_layout(margin={"r":0,"t":30,"l":0,"b":0})

        # 화면을 가득 채우는 설정
        fig.update_layout(
            autosize=True,
            width=1400,    # 필요에 따라 더 크게 조정 가능
            height=800,
            margin=dict(l=0, r=0, t=40, b=0),
            title={
                'text': '도시별 웹서버 접근 수',
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': {
                    'size': 24,
                    'color': 'black',
                    'family': 'Arial'
                }
            }
        )
        
        # 버블맵에 지구 테두리 표시
        fig.update_geos(
            fitbounds="locations",
            visible=True,
            showocean=True,
            oceancolor="LightBlue",
            showland=True,
            landcolor="White",
            showcountries=True,
            countrycolor="Black"
        )
        return fig
    else:
        return no_update
