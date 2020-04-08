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
        html.P(["""This dashboard is meant to allow easy visualization of statistics related to Covid19. Main contribution
        is the addition of testing statistics for Latin American countries, which I collect manually each day from
        press releases. This dashboard is open-sourced on Github, and you can view/contribute """,
        html.A('here.', href='https://github.com/abishalom/Covid19_Analysis', target='_blank')]),]
    )),
    dbc.Row(dbc.Col(html.H3('Data Sources'))),
    dbc.Row(dbc.Col(html.P(
        """I individually collect data from Panama, Peru, Ecuador, Costa Rica, Colombia, Chile, Mexico, and South Korea.
        US testing data from covidtracking.com, Italy testing data from the official government Github repository.
        The rest of the data (confirmed cases and deaths) is retrieved from Johns Hopkins github repository.
        """
    )))
])