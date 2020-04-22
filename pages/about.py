import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from app import app

# layout = html.Div([
#     html.H3('About page')
# ])

layout = dbc.Container([
    dbc.Row(dbc.Col(html.H3('About'))),

    dbc.Row(dbc.Col([
        html.P(["""This dashboard is meant to allow easy visualization of statistics related to Covid19.
        This dashboard is built using plotly dash, open-sourced on Github, and you can view/contribute """,
        html.A('here.', href='https://github.com/abishalom/Covid19_Analysis', target='_blank')]),]
    )),
    dbc.Row(dbc.Col(html.H3('Data Sources'))),
    dbc.Row(dbc.Col(html.P(
        """I individually collect data from Peru, Ecuador, Costa Rica, Colombia, and South Korea.
        US testing data from covidtracking.com, Italy testing data from the official government Github repository,
        Chile from government repository, Panama from Github database maintained by c0t088,
        and Mexico from Github database maintaned by carranco-sga.
        The rest of the data (confirmed cases and deaths) is retrieved from Johns Hopkins github repository.
        """
    )))
])