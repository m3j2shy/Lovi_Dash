import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Output, Input, callback, dash_table, State, no_update
from dash.exceptions import PreventUpdate 
import pandas as pd
import os
import pandas_gbq
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # Gunicorn이 이 서버 객체를 사용합니다

# BigQuery에서 데이터 로드
project_id = os.getenv('GCP_PROJECT_ID')
dataset = os.getenv('BIGQUERY_DATASET')
table = os.getenv('BIGQUERY_TABLE')

query = f"""
SELECT * FROM `{project_id}.{dataset}.{table}`
"""
df = pandas_gbq.read_gbq(query, project_id=project_id)

# 년도 Dropdown 요소 설정
df2 = df.drop_duplicates(subset=['year', 'city'])[['year', 'city']].reset_index(drop=True)
labels = df2['year'].astype(str) + '(' + df2['city'] + ')'
options = labels.map(lambda x: {'label': x, 'value': int(x.split('(')[0])})

# Layout 설정
header = html.H1('🐶🐹Lovi🐱🐰', className="bg-info p-2 mb-2 text-center")

left = dbc.Card([
    dbc.CardHeader('특정 개최년도에서 국가와 종목을 선택한 데이터 추출', className='fw-bold'),
    dbc.CardBody([
        html.H6('Year'), 
        dcc.Dropdown(options=options, value=options[0]['value'], id='drp_year'),
        html.H6('country'), 
        dcc.Dropdown(id='drp_country'),
        html.Hr(),
        html.Div([
            dcc.RadioItems(options=['all', 'clear'], inline=True, id='rad_all'),
            dcc.Checklist(inline=True, id='chk_sport'),
        ]),
    ], className='d-grid gap-2'),
    dbc.Button('submit', id='btn_submit')
])

right = dbc.Card([
    html.Div('테이블 제목', className='text-center text-primary fw-bold', id='div_title'),
    dash_table.DataTable(data = df.to_dict('records'), page_size=10, id='tbl_table')
], body=True)

app.layout = dbc.Container([
    header,
    dbc.Row([
        dbc.Col(left, width=4),
        dbc.Col(right, width=8)
    ]),
], fluid=True, className = 'dbc')

# Callback 함수 구현
@callback(Output('drp_country', 'options'), Output('drp_country', 'value'), Input('drp_year', 'value'))
def update_country(year):
    if not year:
        return no_update, no_update
    countries = df.query('year == @year')['country'].unique()
    return countries, countries[0]

@callback(Output('chk_sport', 'options'), Output('chk_sport', 'value'), Input('drp_country', 'value'), State('drp_year', 'value'),
          prevent_initial_call=True)
def update_sport(country, year):
    if not country:
        return no_update, no_update
    sports = df.query('country == @country and year == @year')['sport'].unique()
    return sports, [sports[0]]

@callback(Output('div_title', 'children'), Output('tbl_table', 'data'), Input('btn_submit', 'n_clicks'),
          State('drp_year', 'value'), State('drp_country', 'value'), State('chk_sport', 'value'))
def update_table(btn, year, country, sport):
    if not btn or not year or not country or not sport:
        return no_update, no_update
    title = f'{year}년도 {country}국가의 {sport} 종목 데이터'
    data = df.query('year == @year and country == @country and sport in @sport').to_dict('records')
    return title, data

@callback(Output('chk_sport', 'value', allow_duplicate=True), Input('rad_all', 'value'), State('chk_sport', 'options'), prevent_initial_call=True)
def select_all_sport(chk_sport, options):
    if not chk_sport:
        return no_update
    if chk_sport=='all':
        return options
    return []

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port) 