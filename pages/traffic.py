from dash import html, dcc, callback, Output, Input, State, ctx, dash_table, callback_context
import dash_bootstrap_components as dbc
import utils.traffic_utils as tu
import pandas as pd
import plotly.graph_objects as go

min_date_str, max_date_str = tu.get_date_range()
start_date = min_date_str
end_date = max_date_str
traffic_per_day_fig = tu.fig_traffic_per_day(start_date, end_date, 'bar')
traffic_per_hour_fig = tu.fig_traffic_per_hour(start_date, end_date, 'bar')
traffic_per_day_compare_users_fig = tu.fig_traffic_per_day_compare_users(start_date, end_date)
traffic_avg_per_hour_fig = tu.fig_traffic_avg_per_hour(start_date, end_date)
# traffic_predict_fig = tu.fig_traffic_predict(min_date_str, max_date_str)

# 트래픽 분석 페이지 레이아웃 생성
def create_traffic_layout():
    return html.Div([
        html.H2("트래픽 분석", style={"textAlign": "center"}),
        html.Div([
            html.Div([
                # 날짜 선택
                dbc.Row([
                    dbc.Col([
                        html.Label("날짜 범위", className="filter-label"),
                        html.Div([
                            html.Div([
                                html.Label("시작 날짜:", style={"marginRight": "10px", "fontWeight": "normal", "fontSize": "0.9rem"}),
                                dcc.DatePickerSingle(
                                    id='traffic-start-date',
                                    date=min_date_str,
                                    display_format='YYYY-MM-DD'
                                )
                            ], style={"display": "inline-block", "marginRight": "15px"}),
                            html.Div([
                                html.Label("종료 날짜:", style={"marginRight": "10px", "fontWeight": "normal", "fontSize": "0.9rem"}),
                                dcc.DatePickerSingle(
                                    id='traffic-end-date',
                                    date=max_date_str,
                                    display_format='YYYY-MM-DD'
                                )
                            ], style={"display": "inline-block"}),
                        ], style={"display": "flex", "alignItems": "center", "marginTop": "5px"})
                    ], width=6),
                    # 상태 필터
                ])
            ], className="filter-container"),
            
            html.Div([
                # 메인 차트
                html.H4("트래픽 추이"),
                dbc.Row([
                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button("막대 그래프", id="btn-traffic-day-bar", color="primary", outline=True, size="sm", className="me-1", active=True),
                            dbc.Button("선 그래프", id="btn-traffic-day-line", color="primary", outline=True, size="sm")
                        ], size="sm", style={"marginBottom": "5px"}),
                    ], width=3),
                    dcc.Loading(
                        id="loading-traffic-day",
                        type="circle",
                        children=dcc.Graph(id='chart-traffic-day', figure=traffic_per_day_fig)
                    ),
                ]),
                dbc.Row([
                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button("막대 그래프", id="btn-traffic-hour-bar", color="primary", outline=True, size="sm", className="me-1", active=True),
                        dbc.Button("선 그래프", id="btn-traffic-hour-line", color="primary", outline=True, size="sm")
                    ], size="sm", style={"marginBottom": "5px"}),
                    ], width=3),
                    dcc.Loading(
                        id="loading-traffic-hour",
                        type="circle",
                        children=dcc.Graph(id='chart-traffic-hour', figure=traffic_per_hour_fig)
                    )
                ])
            ], className="main-container"),
            
            html.Div([
                # 중간
                dbc.Row([
                    dbc.Col([
                        html.H4("날짜 별 실제 방문자 수 비교"),
                        dcc.Loading(
                            id="loading-traffic-compare-users",
                            type="circle",
                            children=dcc.Graph(id='chart-traffic-day-compare-users', figure=traffic_per_day_compare_users_fig)
                        )
                    ], width=6),
                    dbc.Col([
                        html.H4("시간 별 평균 트래픽"),
                        dcc.Loading(
                            id="loading-traffic-avg",
                            type="circle",
                            children=dcc.Graph(id='chart-traffic-avg', figure=traffic_avg_per_hour_fig)
                        )
                    ], width=6)
                ])
            ], className="detail-container"),

            # html.Div([
            #     # 하단
            #     html.H4("트래픽 예측"),
            #     html.P("최대 48시간 이내의 트래픽을 예측할 수 있습니다."),
            #     dbc.Alert(
            #         html.Span("추천 예측 기간: 날짜 범위의 25~50%"),
            #         color="primary",
            #     ),
            #     dbc.InputGroup(
            #         [
            #             dbc.Input(id='input-traffic-predict-date', type='number', min=1, max=48, step=1, placeholder="예측 시간", value=48
            #                         , style={'display': 'inline', 'marginRight': '10px'}),
            #             dbc.Button("예측", id="btn-traffic-predict", color="primary", size="sm"),
            #         ]
            #     ),
            #     dcc.Loading(
            #         id="loading-traffic-avg",
            #         type="circle",
            #         children=dcc.Graph(id='chart-traffic-predict', figure=traffic_predict_fig)
            #     )
            # ], className="detail-container")
        ], className="page-container")
    ])

layout = create_traffic_layout() 

# callbacks
@callback(
    Output('chart-traffic-day', 'figure', allow_duplicate=True),
    Output('chart-traffic-hour', 'figure', allow_duplicate=True),
    Output('chart-traffic-day-compare-users', 'figure', allow_duplicate=True),
    Output('chart-traffic-avg', 'figure', allow_duplicate=True),
    # Output('chart-traffic-predict', 'figure', allow_duplicate=True),
    Output('btn-traffic-day-bar', 'active', allow_duplicate=True),
    Output('btn-traffic-day-line', 'active', allow_duplicate=True),
    Output('btn-traffic-hour-bar', 'active', allow_duplicate=True),
    Output('btn-traffic-hour-line', 'active', allow_duplicate=True),
    [Input('traffic-start-date', 'date'),
     Input('traffic-end-date', 'date')],
    prevent_initial_call=True
)
def update_traffic_chart(s, e):
    global start_date, end_date
    start_date = s
    end_date = e
    
    traffic_per_day_fig = tu.fig_traffic_per_day(start_date, end_date, 'bar')

    traffic_per_hour_fig = tu.fig_traffic_per_hour(start_date, end_date, 'bar')

    traffic_per_day_compare_users_fig = tu.fig_traffic_per_day_compare_users(start_date, end_date)

    traffic_avg_per_hour_fig = tu.fig_traffic_avg_per_hour(start_date, end_date)

    # traffic_predict_fig = tu.fig_traffic_predict(start_date, end_date)

    return traffic_per_day_fig, traffic_per_hour_fig, traffic_per_day_compare_users_fig, traffic_avg_per_hour_fig, True, False, True, False


# 상단
@callback(
    [Output('chart-traffic-day', 'figure', allow_duplicate=True),
    Output('btn-traffic-day-bar', 'active', allow_duplicate=True),
    Output('btn-traffic-day-line', 'active', allow_duplicate=True)],
    [Input('btn-traffic-day-bar', 'n_clicks'),
     Input('btn-traffic-day-line', 'n_clicks')],
    prevent_initial_call=True
)
def update_traffic_day_chart(n_clicks_day_bar, n_clicks_day_line):
    ctx = callback_context
    if ctx.triggered[0]['prop_id'] == 'btn-traffic-day-bar.n_clicks':
        traffic_per_day_fig = tu.fig_traffic_per_day(start_date, end_date, 'bar')
        return traffic_per_day_fig, True, False
    elif ctx.triggered[0]['prop_id'] == 'btn-traffic-day-line.n_clicks':
        traffic_per_day_fig = tu.fig_traffic_per_day(start_date, end_date, 'line')
        return traffic_per_day_fig, False, True

@callback(
    Output('chart-traffic-hour', 'figure', allow_duplicate=True),
    Output('btn-traffic-hour-bar', 'active', allow_duplicate=True),
    Output('btn-traffic-hour-line', 'active', allow_duplicate=True),
    [Input('btn-traffic-hour-bar', 'n_clicks'),
     Input('btn-traffic-hour-line', 'n_clicks')],
     prevent_initial_call=True
)
def update_traffic_hour_chart(n_clicks_hour_bar, n_clicks_hour_line):
    ctx = callback_context
    if ctx.triggered[0]['prop_id'] == 'btn-traffic-hour-bar.n_clicks':
        traffic_per_hour_fig = tu.fig_traffic_per_hour(start_date, end_date, 'bar')
        return traffic_per_hour_fig, True, False
    elif ctx.triggered[0]['prop_id'] == 'btn-traffic-hour-line.n_clicks':
        traffic_per_hour_fig = tu.fig_traffic_per_hour(start_date, end_date, 'line')
        return traffic_per_hour_fig, False, True
    
# 하단
# @callback(
#     Output('btn-traffic-predict', 'disabled', allow_duplicate=True),
#     Input('input-traffic-predict-date', 'value'),
#     prevent_initial_call=True
# )
# def update_traffic_predict_date(value):
#     if value:
#         if 1 <= int(value) <= 48:
#             return False
#     return True

# @callback(
#     Output('chart-traffic-predict', 'figure', allow_duplicate=True),
#     Input('btn-traffic-predict', 'n_clicks'),
#     State('input-traffic-predict-date', 'value'),
#     prevent_initial_call=True
# )
# def update_traffic_predict(n_clicks, predict_date):
#     if predict_date is None:
#         predict_date = 24  # Default value if None
#     try:
#         predict_date = int(predict_date)
#         if not 1 <= predict_date <= 48:
#             return traffic_predict_fig
#         if n_clicks > 0:
#             traffic_predict_fig = tu.fig_traffic_predict(min_date_str, max_date_str, predict_date)
#             return traffic_predict_fig
#     except (ValueError, TypeError):
#         return traffic_predict_fig
#     return traffic_predict_fig
