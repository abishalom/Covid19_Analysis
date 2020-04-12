import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from app import app

# layout = html.Div([
#     html.H3('About page')
# ])

layout = dbc.Container([
    dbc.Row(dbc.Col(html.H3('Analysis'))),

    dbc.Row(dbc.Col(html.P('Quick Antibody Test Mental Math')))

])