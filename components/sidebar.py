from dash import html
import dash_bootstrap_components as dbc
from constants import NAV_LINKS

def create_sidebar():
    """
    사이드바 컴포넌트를 생성하는 함수
    
    Returns:
        html.Div: 사이드바 컴포넌트
    """
    return html.Div(
        [
            html.Div([
                html.Img(
                    src="assets/image.webp",
                    alt="Lovi Logo",
                    className="sidebar-logo mb-4"
                ),
                html.H3("🐶🐹🐱🐰", className="text-center mb-4"),
                html.Hr(),
                dbc.Nav(
                    [
                        dbc.NavLink(
                            [html.Span(link["icon"], className="nav-icon"), 
                             html.Span(link["label"], className="nav-text")],
                            href=link["href"],
                            active="exact",
                            className="nav-link",
                        ) for link in NAV_LINKS
                    ],
                    vertical=True,
                    pills=True,
                ),
            ], className="sidebar-content"),
            html.Div(
                dbc.Button(
                    "◀",
                    id="sidebar-toggle",
                    className="sidebar-toggle",
                    color="secondary",
                    size="sm",
                ),
            ),
        ],
        id="sidebar",
        className="sidebar",
    ) 