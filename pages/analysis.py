import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from app import app

# layout = html.Div([
#     html.H3('About page')
# ])

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
        dbc.Label('Antibody Probability'),
        dbc.Input(type='number', min = 0.0, max=1.0, value = 0.35, id = 'AP', step = 0.000001)
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
    Insert the estimated sensitivity and specificity of the test, along with an estimate for the antibody prevalence in the population.
    Note: if you cannot have antibodies without getting infected, this number should be approximately (asymptomatic patients)/(population) in a given country/region.
    """))),
    dbc.Row([
        dbc.Col(controls, md=4),
        dbc.Col(html.Div(id = 'results'), md=8)
    ])
])


@app.callback(
    Output('results', 'children'),
    [Input('TPR', 'value'), Input('TNR', 'value'), Input('AP', 'value'), Input('num_tests', 'value')]
)
def get_probs(TPR, TNR, AP, num_tests):
    FPR = 1 - TNR
    FNR = 1- TPR
    prob_anti_pos_test =  (TPR**num_tests * AP)/(TPR**num_tests * AP + FPR**num_tests * (1-AP))
    prob_noanti_neg_test = (TNR**num_tests * (1-AP))/(TNR**num_tests * (1-AP) + FNR**num_tests * AP)

    s1 = 'Probablity of having antibodies after testing positive {} time(s): {:.6f}'.format(num_tests, prob_anti_pos_test)
    s2 = 'Probability of NOT having antibodies after testing negative {} time(s): {:.6f}'.format(num_tests, prob_noanti_neg_test)

    return html.P([s1, html.Br(), s2])