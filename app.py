import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Output, Input, callback, State
import os
import socket
import platform

# 컴포넌트와 유틸리티 임포트
from components.sidebar import create_sidebar
from utils import create_404_page
from constants import PAGE_MODULES

from pages import home, traffic, visitor_analysis, referrer, region, management, about

# 개발/배포 환경 구분
HOSTNAME = socket.gethostname()
LOCAL_HOSTNAMES = ['DESKTOP', 'LAPTOP', 'MIN', 'WIN', 'PC', 'LOCAL']
IS_LOCAL = (
    any(name in HOSTNAME.upper() for name in LOCAL_HOSTNAMES)
    or platform.system() in ['Windows', 'Darwin']  # Windows, Mac
    or os.environ.get('IS_LOCAL', '').lower() == 'true'
)

# 개발 환경에서만 기본 핫 리로드 설정
if IS_LOCAL:
    os.environ['DASH_DEBUG'] = 'true'
    os.environ['DASH_HOT_RELOAD'] = 'true'

# Dash 앱 초기화
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    assets_folder='assets'
)

server = app.server

# 레이아웃 설정
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    create_sidebar(),
    html.Div(id='page-content', className="content")
])

# 사이드바 토글 콜백
@app.callback(
    [Output("sidebar", "className"),
     Output("page-content", "className"),
     Output("sidebar-toggle", "children")],
    [Input("sidebar-toggle", "n_clicks")],
    [State("sidebar", "className"),
     State("page-content", "className"),
     State("sidebar-toggle", "children")]
)
def toggle_sidebar(n_clicks, sidebar_class, content_class, toggle_text):
    if n_clicks is None:
        return sidebar_class, content_class, toggle_text
    
    if "collapsed" not in sidebar_class:
        return "sidebar collapsed", "content collapsed", "▶"
    else:
        return "sidebar", "content", "◀"

# 페이지 라우팅 콜백
@callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    try:
        if pathname in PAGE_MODULES:
            module_name = PAGE_MODULES[pathname]
            module = globals()[module_name]
            return module.layout
        else:
            return create_404_page()
    except Exception:
        return create_404_page()

app.index_string = '''
<!DOCTYPE html>
<html lang="ko">
    <head>
        {%metas%}
        <title>Lovi Dashboard - 웹사이트 분석 대시보드</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta name="description" content="Lovi Dashboard는 웹사이트 트래픽, 사용자 행동, 유입 출처 등을 분석하는 대시보드입니다.">
        <meta name="keywords" content="대시보드, 웹분석, 트래픽, 사용자분석, 유입출처">
        <meta name="author" content="Lovi Team">
        <meta property="og:title" content="Lovi Dashboard">
        <meta property="og:description" content="웹사이트 분석 대시보드">
        <meta property="og:type" content="website">
        <meta property="og:url" content="https://lovi.my">
        <meta property="og:image" content="https://lovi.my/assets/LOVi_logo_whiteLine.png">
        <meta property="og:image:width" content="1200">
        <meta property="og:image:height" content="630">
        <meta property="og:image:alt" content="LOVi 로고">
        <meta name="twitter:card" content="summary_large_image">
        <meta name="twitter:image" content="https://lovi.my/assets/LOVi_logo_whiteLine.png">
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# 앱 실행
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    
    if IS_LOCAL:
        app.run(debug=True, dev_tools_hot_reload=True)
    else:
        app.run(debug=False, host='0.0.0.0', port=port) 