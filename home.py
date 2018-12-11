import dash_core_components as dcc
import dash_html_components as html

layout = html.Div(children=[
    html.H2('Data Processing, Visualisation', style={'textAlign': 'center'}),
    html.H4('Prehľad dostupných dát'),
    dcc.Link('Dáta spoločnosti 4dot', href='/visualisation/tdms', style={'margin-left': '35px'}),
    html.Br(),
    dcc.Link('Verejne dostupné datasety', href='/visualisation/mat', style={'margin-left': '35px'}),
    html.Br(),
    dcc.Link('Device local', href='/visualisation/4dot', style={'margin-left': '35px'}),

], style={'margin-left': '35px'},
)
