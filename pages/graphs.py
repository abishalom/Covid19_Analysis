import plotly.express as px
import numpy as np
import pandas as pd
import DataClean
import datetime
import os
import pickle
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from app import app

dat = pickle.load(open('compiled_data.p', 'rb'))
countries = list(dat.index.get_level_values(0).unique())
stats = list(dat.columns)
stat_map = {
    'DailyPosTestRate': 'Daily Positive Test Rate',
    'Confirmed': 'Confirmed Tests',
    'NewTests': 'Daily New Tests',
    'CumulativePosTestRate': 'Cumulative Positive Test Rate',
    'NewCases': 'New Cases',
    'TotalTests': 'Total Tests',
    'ConfirmedGrowth': 'Daily Confirmed Cases Growth (%)',
    'CumulativeDeathRate': 'Cumulative Death Rate',
    'HospitalizationRate': 'Hospitalization Rate',
    'TotalTestsPer10k': 'Total Tests per 10k Population',
    'ConfirmedPer10k': 'Total Confirmed per 10k Population',
    'NewTestsPer10k': 'Daily Tests per 10k Population'
}

xs = ['DaysSinceFirst', 'Date', 'DaysSinceTenthDeath', 'DaysSinceShutdown']
xs_map = {'DaysSinceFirst': 'Days Since First Confirmed',
         'DaysSinceTenthDeath': 'Days Since 10th Death',
         'DaysSinceShutdown': 'Days Since Economic Shutdown'}

#Makes graphs
def make_graph(count_to_plot, stat_to_plot, x_axis):
    to_add = ['Date'] if x_axis != 'Date' else []
    to_plot = dat.reset_index()
    to_plot = to_plot[to_plot.Country.isin(count_to_plot)][['Country'] + [stat_to_plot] + [x_axis] +to_add ]
    if x_axis != 'Date':
        to_plot['Date'] = to_plot['Date'].dt.strftime('%b %d, %Y')

    def add_styling(plot_fig):
        plot_fig.update_xaxes(title = xs_map.get(x_axis, x_axis))
        plot_fig.update_yaxes(title = stat_to_plot)
        return plot_fig

    #generate a plot of each type, save in a dict.
    plots = {}

    plots['scatter'] = add_styling(
        px.scatter(to_plot,
            x = to_plot[x_axis],
            y = to_plot[stat_to_plot],
            color = to_plot.Country,
            hover_data = ['Date'] if x_axis != 'Date' else [],
            title = '{} by Country'.format(stat_map.get(stat_to_plot, stat_to_plot)))
    )

    plots['bar'] = add_styling(
        px.bar(to_plot,
            x = to_plot[x_axis],
            y = to_plot[stat_to_plot],
            color = to_plot.Country,
            barmode = 'group',
            hover_data = ['Date'] if x_axis != 'Date' else [],
            title = '{} by Country'.format(stat_map.get(stat_to_plot, stat_to_plot)))
    )

    plots['line'] = add_styling(
        px.line(to_plot,
            x = to_plot[x_axis],
            y = to_plot[stat_to_plot],
            color = to_plot.Country,
            hover_data = ['Date'] if x_axis != 'Date' else [],
            title = '{} by Country'.format(stat_map.get(stat_to_plot, stat_to_plot)))
    )
    return plots

layout = dbc.Container([
    dcc.Store(id='graphs-store'),

    dbc.Tabs([
        dbc.Tab(label = 'Scatter', tab_id = 'scatter'),
        dbc.Tab(label = 'Bar', tab_id='bar'),
        dbc.Tab(label= 'Line', tab_id='line')
    ], id = 'tabs'),

    html.Div([
        dbc.Row([
            dbc.Col(dbc.Button('Refresh', id = 'refresh-button', n_clicks=0,  block=True)),
            dbc.Col(html.Div(id='refresh-time'), align='right')
        ])
    ]),
    # html.Div([
    #     # html.Button('Refresh', id = 'refresh-button', n_clicks=0, style = {'height': '50px', 'width':'300px'})
    #     dbc.Button('Refresh', id = 'refresh-button', n_clicks=0,  block=True)
    # ], style = {'width': '50%', 'display': 'inline-block', 'align':'center'}),

    # html.Div([
    #     html.P(id='refresh-time')
    # ], style = {'width': '50%', 'display': 'inline-block', 'align':'right'}),

    # html.Div([
    #     html.H4('Please hit "Reset axis" button after changing x-axis on plots; button in top right corner of each plot, shaped like house.'),
    #     html.H4('You can also pan, zoom, and hover over datapoints in the plots.')
    # ]),

    html.Div([
        dbc.Row(
            [
            dbc.Col(html.Div("Countries:"), width=4),
            dbc.Col(html.Div("Statistics:"), width=5),
            dbc.Col(html.Div("X-Axis:"), width=3)
            ],
            justify="center",
            align='center'
        ),
        dbc.Row(
            [
            dbc.Col(
                [dcc.Dropdown(
                id = 'country-select',
                options = [{'label': stat_map.get(c, c), 'value': c} for c in countries],
                value = ['Panama'],
                multi = True
                )],
            width = 4),
            dbc.Col(
                [dcc.Dropdown(
                    id = 'statistic-select',
                    options = [{'label': stat_map.get(s, s), 'value': s} for s in stats],
                    value = ['Confirmed'],
                    multi=True
                )],
            width = 5),
            dbc.Col(
                [dcc.Dropdown(
                    id = 'x-axis-select',
                    options = [{'label': xs_map.get(x, x), 'value': x} for x in xs],
                    value = 'DaysSinceFirst',
                    multi=False
                )],
            width = 3),],
        justify = 'center',
        align='center')
    ]),

    html.Div(id='tab-content'),

    html.Div([
        dbc.Row(dbc.Col([
            html.P("Please hit 'reset axis' button after changing x-axis on plots; this button is top-right corner, shaped like a house."),
            html.P("You can interact with plots by panning, zooming, and hovering over datapoints."),
        ]))
    ]),

], className = 'dash-bootstrap', fluid=True
)



#Generate the graphs for ALL types
@app.callback(
    Output('graphs-store', 'data'),
    [Input('country-select', 'value'), Input('statistic-select', 'value'),
    Input('x-axis-select', 'value')]
)
def update_graph(countries, stats, x_axis):
    #Returns a list of graphs
    graph_types = ['scatter', 'bar', 'line']
    all_graphs = {i: [] for  i in graph_types}

    for plot_stat in stats:
        gs = make_graph(countries, plot_stat, x_axis)
        for i,g in gs.items():
            all_graphs[i].append(dcc.Graph(figure=g,
                                    id = '{}_{}'.format(plot_stat, i),
                                    animate = True))
    return all_graphs


@app.callback(
    Output('tab-content', 'children'),
    [Input('tabs', 'active_tab'), Input('graphs-store', 'data')]
)
def render_tab_content(active_tab, data):
    """
    Takes active tab and stored graphs as input, renders tab content depending on value of active tab.
    """
    if active_tab and data is not None:
            return [dbc.Row(dbc.Col(g)) for g in data[active_tab]]
            # dbc.Col(
            #     [dbc.Row(g) for g in data[active_tab]],
            # )
    # return dbc.Col(data[active_tab][0])

    # return data


#Get the last refreshed time and return it
@app.callback(Output('refresh-time', 'children'),
             [Input('refresh-button', 'n_clicks')])
def on_click(n_clicks):
    timezone = datetime.datetime.now().astimezone().strftime('%Z')
    if n_clicks >= 1:
        DataClean.data_clean('compiled_data.p')

    dat = pickle.load(open('compiled_data.p', 'rb'))

    t = datetime.datetime.fromtimestamp(os.path.getmtime('compiled_data.p'))
    return 'Last refresh: {} {}'.format(t.strftime('%Y-%b-%d, %H:%M:%S'), timezone)