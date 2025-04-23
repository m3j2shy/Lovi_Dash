import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Output, Input, callback, State
import os
import socket
import datetime
import sys

# 컴포넌트와 유틸리티 임포트
from components.sidebar import create_sidebar
from utils import create_404_page
from constants import PAGE_MODULES

# 페이지 모듈 미리 임포트
from pages import home, traffic, user_analysis, popular_keywords, referrer, region, management, about

# 환경 확인 - 호스트명으로 로컬/도커 환경 구분
HOSTNAME = socket.gethostname()
IS_LOCAL = 'DESKTOP' in HOSTNAME or 'LAPTOP' in HOSTNAME

# 개발 모드에서 자동 리로드 강제 활성화 - 앱 생성 전에 환경 변수 설정
if IS_LOCAL:
    os.environ['DASH_HOT_RELOAD'] = 'true'
    os.environ['DASH_HOT_RELOAD_INTERVAL'] = '100'
    os.environ['DASH_HOT_RELOAD_WATCH_INTERVAL'] = '100'
    os.environ['DASH_HOT_RELOAD_MAX_RETRY'] = '30'
    os.environ['DASH_DEBUG'] = 'true'

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    suppress_callback_exceptions=True,
    assets_folder='assets',
    update_title='로딩 중...'
)

# 로컬 개발 환경에서 추가 설정
if IS_LOCAL:
    app.config.suppress_callback_exceptions = True
    app.config.assets_ignore = r'.*\.(py|pyc)$'

server = app.server

# 레이아웃을 함수로 정의하여 매번 새로 생성하도록 함
def serve_layout():
    # 현재 시간을 숨겨진 div에 포함시켜 매번 레이아웃이 새로 생성되도록 함
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    
    return html.Div([
        dcc.Location(id='url', refresh=False),
        # 핫 리로드 강제 트리거를 위한 인터벌 컴포넌트
        dcc.Interval(
            id='hot-reload-trigger',
            interval=1000,  # 1초마다
            n_intervals=0
        ),
        create_sidebar(),
        html.Div(id='page-content', className="content"),
        html.Div(timestamp, id='timestamp', style={'display': 'none'})
    ])

# 레이아웃을 함수로 설정
app.layout = serve_layout

# 자동 리로드 트리거 콜백
@app.callback(
    Output('timestamp', 'children'),
    Input('hot-reload-trigger', 'n_intervals')
)
def update_timestamp(n):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    return timestamp

# 사이드바 토글 콜백
@app.callback(
    [Output("sidebar", "className"),
     Output("page-content", "className"),
     Output("sidebar-toggle", "children")],
    [Input("sidebar-toggle", "n_clicks")],
    [State("sidebar", "className"),
     State("page-content", "className"),
     State("sidebar-toggle", "children")],
)
def toggle_sidebar(n_clicks, sidebar_class, content_class, toggle_text):
    if n_clicks is None:
        return sidebar_class, content_class, toggle_text
    
    if "collapsed" not in sidebar_class:
        return "sidebar collapsed", "content collapsed", "▶"
    else:
        return "sidebar", "content", "◀"

# 페이지 콘텐츠를 로드하는 콜백
@callback(Output('page-content', 'children'),
          [Input('url', 'pathname'),
           Input('timestamp', 'children')])
def display_page(pathname, timestamp):
    try:
        # 각 모듈 다시 임포트
        if pathname in PAGE_MODULES:
            module_name = PAGE_MODULES[pathname]
            import importlib
            
            # 이전에 임포트된 모듈 명시적으로 캐시에서 제거
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            # 모듈 다시 임포트
            if module_name in globals():
                module = importlib.reload(globals()[module_name])
                return module.layout
            else:
                return create_404_page()
        else:
            return create_404_page()
    except Exception as e:
        return create_404_page()

# CSS 스타일 추가 - 간소화된 템플릿 사용
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    
    if IS_LOCAL:
        # 로컬 환경에서는 디버그 모드 활성화
        app.run(
            debug=True,
            dev_tools_hot_reload=True,
            dev_tools_hot_reload_interval=100,        # 0.1초로 조정 (부하 감소)
            dev_tools_hot_reload_watch_interval=100,  # 0.1초로 조정 (부하 감소)
            dev_tools_hot_reload_max_retry=30,
            dev_tools_ui=True,                        # 디버그 UI 활성화
            use_reloader=True,                        # 리로더 명시적 활성화
            dev_tools_props_check=True,
            dev_tools_serve_dev_bundles=True,         # 개발 번들 사용
            dev_tools_prune_errors=True,              # 오류 스택트레이스 간소화
            dev_tools_silence_routes_logging=True     # 라우트 로깅 비활성화 (콘솔 깔끔하게)
        )
    else:
        # Docker나 프로덕션 환경에서는 디버그 비활성화
        app.run(
            debug=False,
            host='0.0.0.0',
            port=port
        ) 