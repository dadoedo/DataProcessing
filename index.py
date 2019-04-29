import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import home
from app import app
from tdms import tdms, mat
from device import history, realTime

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])

server = app.server

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    pathnameArray = str(pathname).split('/')
    if len(pathnameArray) > 1:
        if pathnameArray[1] == "device":
            if pathnameArray[2] == "history":
                return history.returnLayout(pathnameArray[3])
            if pathnameArray[2] == "realtime":
                return realTime.returnLayout()
    if pathname == '/visualisation/tdms':
        return tdms.layout
    elif pathname == '/visualisation/mat':
        return mat.layout
    elif pathname == '/visualisation/4dot':
        return history.layout
    else:
        return home.layout


if __name__ == '__main__':
    app.run_server(threaded=False, debug=False)
