import dash_bootstrap_components as dbc
from dash import Dash, html, dcc, Output, Input, callback, State
import os

# 컴포넌트와 유틸리티 임포트
from components.sidebar import create_sidebar
from utils import create_404_page
from constants import PAGE_MODULES

# 페이지 모듈 미리 임포트
from pages import home, traffic, user_analysis, popular_keywords, referrer, region, management, about

app = Dash(__name__, 
           external_stylesheets=[dbc.themes.BOOTSTRAP],
           suppress_callback_exceptions=True)
server = app.server

# 기본 레이아웃 설정
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
          Input('url', 'pathname'))
def display_page(pathname):
    try:
        if pathname in PAGE_MODULES:
            module_name = PAGE_MODULES[pathname]
            module = globals()[module_name]
            return module.layout
        else:
            return create_404_page()
    except Exception as e:
        print(f"페이지 로딩 중 에러 발생: {e}")
        return create_404_page()

# CSS 스타일 추가
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
    app.run(debug=False, host='0.0.0.0', port=port) 