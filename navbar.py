import dash_bootstrap_components as dbc

navbar = dbc.NavbarSimple(
    children  = [
        dbc.NavItem(dbc.NavLink('Graphs', href='/graphs')),
        dbc.NavItem(dbc.NavLink('Analysis', href='/analysis')),
        dbc.NavItem(dbc.NavLink('About', href='/about'))
    ],
    brand = 'Abi-Covid19-Tracker',
    brand_href='/graphs',
    color = 'primary',
    dark = True,
    sticky='top'
)