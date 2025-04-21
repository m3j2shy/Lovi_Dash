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

# 전체 query 사용시 limit 추가 필수
# 일반적인 경우 where 조건 추가하여 호출
# (어차피 데이터 양이 많아서 전체 데이터 조회 시 쿼리 중간에 터짐)
query = f"""
SELECT * FROM `{project_id}.{dataset}.{table}` limit 1000
"""
df = pandas_gbq.read_gbq(query, project_id=project_id)
print(df.head())

# Layout 설정
header = html.H1('🐶🐹Lovi🐱🐰', className="bg-info p-2 mb-2 text-center")

left = dbc.Card([
])

right = dbc.Card([
], body=True)

app.layout = dbc.Container([
    header,
    dbc.Row([
        dbc.Col(left, width=4),
        dbc.Col(right, width=8)
    ]),
], fluid=True, className = 'dbc')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port) 