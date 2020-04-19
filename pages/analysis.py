import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pickle
import pandas as pd

from app import app

# layout = html.Div([
#     html.H3('About page')
# ])
dat = pickle.load(open('data/compiled_data.p', 'rb'))
countries = list(dat.index.get_level_values(0).unique())


controls = dbc.Card([
    dbc.FormGroup([
        dbc.Label("Sensitivity (True Positive Rate)"),
        dbc.Input(type='number', min = 0.0, max = 1.0, id = 'TPR', value = 0.9, step = 0.000001)
    ]),

    dbc.FormGroup([
        dbc.Label('Specificity (True Negative Rate)'),
        dbc.Input(type='number', min = 0.0, max = 1.0, id = 'TNR', value = 0.9, step = 0.000001)
    ]),

    dbc.FormGroup([
        dbc.Label('Fraction of Asymptomatic Cases'),
        dbc.Input(type='number', min = 0.0, max=1.0, value = 0.35, id = 'asymp_pct', step = 0.000001)
    ]),

    dbc.FormGroup([
        dbc.Label('Country'),
        dcc.Dropdown(id='country',
                options = [{'label': c, 'value': c} for c in countries],
                value = 'Panama')
    ]),

    dbc.FormGroup([
        dbc.Label('Tests Performed'),
        dbc.Input(type='number', min =  1, step=1, id = 'num_tests', value = 1)
    ])
])

layout = dbc.Container([
    dbc.Row(dbc.Col(html.H3('Analysis'))),

    dbc.Row(dbc.Col(html.H5('Quick Antibody Test Mental Math'))),
    dbc.Row(dbc.Col(html.P("""A tool for using Bayes Rule to ballpark the usefulness of antibody test results.
    Insert the estimated sensitivity and specificity of the test, along with an estimate for the percentage of coronavirus cases that are asymptomatic.
    We assume that all confirmed patients are not included under the asymptomatic population. We also assume each new test done is independent of the previous one.
    Finally, we assume that only patients that have been previously infected are able to develop the antibodies needed.
    """))),
    dbc.Row([
        dbc.Col(controls, md=4),
        dbc.Col(html.Div(id = 'results'), md=8)
    ])
])


@app.callback(
    Output('results', 'children'),
    [Input('TPR', 'value'), Input('TNR', 'value'), Input('asymp_pct', 'value'), Input('country',  'value'), Input('num_tests', 'value')]
)
def get_probs(TPR, TNR, asymp_pct, country, num_tests):
    try:
        country_data = dat.xs(country, level=0)[['Confirmed', 'Population']].tail(1)
        pop = country_data['Population'].sum()
        conf = country_data['Confirmed'].sum()

        tot_cases = min(conf/(1-asymp_pct), pop)
        AP = tot_cases/pop

        FPR = 1 - TNR
        FNR = 1- TPR
        prob_anti_pos_test =  (TPR**num_tests * AP)/(TPR**num_tests * AP + FPR**num_tests * (1-AP))
        prob_noanti_neg_test = (TNR**num_tests * (1-AP))/(TNR**num_tests * (1-AP) + FNR**num_tests * AP)

        s0 = 'Assumptions imply {:.0f} total cases of Covid-19. This represents {:.4f}% of the population.'.format(tot_cases, AP * 100)
        s1 = 'Probablity of having antibodies after testing positive {} time(s): {:.6f}'.format(num_tests, prob_anti_pos_test)
        s2 = 'Probability of NOT having antibodies after testing negative {} time(s): {:.6f}'.format(num_tests, prob_noanti_neg_test)

        return html.P([s0, html.Br(), s1, html.Br(), s2])
    except TypeError:
        return html.P([''])