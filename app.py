import plotly.express as px
import numpy as np
import pandas as pd
import DataClean
import datetime
import os
import pickle
import dash
import dash_core_components as dcc
import dash_html_components as html

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
    'TotalTestsPer10k': 'Total Tests per 10k Population'
}

xs = ['DaysSinceFirst', 'Date', 'DaysSinceTenthDeath', 'DaysSinceShutdown']
xs_map = {'DaysSinceFirst': 'Days Since First Confirmed',
         'DaysSinceTenthDeath': 'Days Since 10th Death',
         'DaysSinceShutdown': 'Days Since Economic Shutdown'}

#Makes graphs
def make_graph(count_to_plot, stat_to_plot, x_axis, plot_style = 0, m=None):
    to_add = ['Date'] if x_axis != 'Date' else []
    to_plot = dat.reset_index()
    to_plot = to_plot[to_plot.Country.isin(count_to_plot)][['Country'] + [stat_to_plot] + [x_axis] +to_add ]
    if x_axis != 'Date':
        to_plot['Date'] = to_plot['Date'].dt.strftime('%b %d, %Y')

    if plot_style == 0:
        fig = px.scatter(to_plot,
                         x = to_plot[x_axis],
                         y = to_plot[stat_to_plot],
                         color = to_plot.Country,
                         hover_data = ['Date'] if x_axis != 'Date' else [],
                         title = '{} by Country'.format(stat_map.get(stat_to_plot, stat_to_plot)))
    elif plot_style == 1:
        fig = px.bar(to_plot, 
                         x = to_plot[x_axis],
                         y = to_plot[stat_to_plot],
                         color = to_plot.Country,
                         barmode = 'group',
                         hover_data = ['Date'] if x_axis != 'Date' else [],
                         title = '{} by Country'.format(stat_map.get(stat_to_plot, stat_to_plot)))
    elif plot_style == 2:
        fig = px.line(to_plot,
                         x = to_plot[x_axis],
                         y = to_plot[stat_to_plot],
                         color = to_plot.Country,
                         hover_data = ['Date'] if x_axis != 'Date' else [],
                         title = '{} by Country'.format(stat_map.get(stat_to_plot, stat_to_plot)))
#     fig.add_trace(tr)

    fig.update_xaxes(title = xs_map.get(x_axis, x_axis))
    fig.update_yaxes(title = stat_to_plot)

    if m is not None:
        x_lim = to_plot.reset_index().groupby('Country')[x_axis].max().min() * m
        y_lim = to_plot.reset_index().groupby('Country')[stat_to_plot].max().min() * m
        fig.update_xaxes(range = [0, x_lim])
        fig.update_yaxes(range = [0, y_lim])

    return fig

app = dash.Dash('Covid-Tracking')
server = app.server

app.layout = html.Div([
    html.Div([
        html.H2('COVID-19 Tracking',),
    ], style = {'width': '40%', 'display': 'inline-block'}),

    html.Div([
        html.P(id='refresh-time')
    ], style = {'width': '40%', 'display': 'inline-block', 'align':'center'}),

    html.Div([
        html.Button('Refresh', id = 'refresh-button', n_clicks=0)
    ], style = {'width': '20%', 'display': 'inline-block', 'align':'right'}),


    html.Div([
        html.H4('Please hit "Reset axis" button after changing x-axis on plots; button in top right corner of each plot, shaped like house.'),
        html.H4('You can also pan, zoom, and hover over datapoints in the plots.')
    ]),
    html.Div([
        html.P(["Countries:",
            dcc.Dropdown(
                id = 'country-select',
    #             options = countries,
                options = [{'label': stat_map.get(c, c), 'value': c} for c in countries],
                value = ['Panama'],
                multi = True
            )
        ]),
    ], style = {"width": "30%", 'display': 'inline-block', 'text-align': 'center'} ),
    html.Div([
        html.P(["Statistics:",
            dcc.Dropdown(
                id = 'statistic-select',
                options = [{'label': stat_map.get(s, s), 'value': s} for s in stats],
                value = ['Confirmed'],
                multi=True
            )
        ])
    ], style = {'width':'30%', 'display':'inline-block', 'text-align': 'center'}),
    html.Div([
        html.P(["X-Axis:",
            dcc.Dropdown(
                id = 'x-axis-select',
                options = [{'label': xs_map.get(x, x), 'value': x} for x in xs],
                value = 'DaysSinceFirst',
                multi=False
            )
        ])
    ], style = {'width':'20%', 'display':'inline-block', 'text-align': 'center'}),
    html.Div([
        html.P(["Graph Style:",
            dcc.Dropdown(
                id = 'graph-style',
                options = [{'label': 'Scatter', 'value': 0}, 
                           {'label': 'Bar' , 'value': 1},
                           {'label': 'Line', 'value': 2}],
                value = 0,
                multi=False
            )
        ])
    ], style = {'width':'20%', 'display':'inline-block', 'text-align': 'center'}),

    html.Div(children = html.Div(id='graphs'), className = 'row', style = {"display":'inline-block', 'width': '100%'}),

    html.Div([
        html.P(['Testing data available for: Panama, Ecuador, Peru, Costa Rica, Italy, US, South Korea. Limited data available for Colombia.']),
        html.P(['Most data on confirms and deaths from Johns Hopkins. US data from covidtracking.com, Italy data from official repo. Other data independently gathered']),
    ])
#     dcc.Graph(id='graphs', style = {'width': '80%', 'display': 'inline-block'}),
], className = 'container'
)

@app.callback(
    dash.dependencies.Output('graphs', 'children'),
    [dash.dependencies.Input('country-select', 'value'), dash.dependencies.Input('statistic-select', 'value'),
    dash.dependencies.Input('x-axis-select', 'value'), dash.dependencies.Input('graph-style', 'value')]
)
def update_graph(countries, stats, x_axis, graph_style):
    if len(stats)>2:
        class_choice = 'col s12 m6 l4'
    elif len(stats) == 2:
        class_choice = 'col s12 m6 l6'
    else:
        class_choice = 'col s12'
    #Returns a list of graphs
    graphs = []
#     return make_graph(countries, stats[0], scatter=False)
    for plot_stat in stats:
        g = make_graph(countries, plot_stat, x_axis, plot_style=graph_style)
        graphs.append(html.Div(dcc.Graph(
            id = plot_stat,
            animate = True,
            figure = g
            ), className = class_choice
        ))
    return graphs

@app.callback(dash.dependencies.Output('refresh-time', 'children'),
             [dash.dependencies.Input('refresh-button', 'n_clicks')])
def on_click(n_clicks):
    if n_clicks >= 1:
        DataClean.data_clean('compiled_data.p')
    t = datetime.datetime.fromtimestamp(os.path.getmtime('compiled_data.p'))
    return 'Last refresh: {}'.format(t.strftime('%Y-%b-%d, %H:%M:%S'))

if __name__ == "__main__":
    app.run_server()
