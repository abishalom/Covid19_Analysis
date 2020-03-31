import dash_bootstrap_components as dbc
import dash
# external_stylesheets =  [dbc.themes.DARKLY]
external_stylesheets=[]
app = dash.Dash('Covid-Tracking', external_stylesheets= external_stylesheets)
server = app.server
app.config.suppress_callback_exceptions = True

# if __name__ == "__main__":
#     app.run_server()
