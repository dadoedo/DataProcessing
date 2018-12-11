import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import home
from app import app
from visualisation import tdms, mat, fourdot

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/visualisation/tdms':
        return tdms.layout
    elif pathname == '/visualisation/mat':
        return mat.layout
    elif pathname == '/visualisation/4dot':
        return fourdot.layout
    else:
        return home.layout


if __name__ == '__main__':
    app.run_server(debug=True)
