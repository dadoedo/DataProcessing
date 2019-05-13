import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import home

from app import app
from device import history, realTime

server = app.server

# URL = /device/{realtime|history}/{deviceID}
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    pathnameArray = str(pathname).split('/')
    if len(pathnameArray) > 1:
        if pathnameArray[1] == "device":
            if pathnameArray[2] == "history":
                return history.returnLayout(pathnameArray[3])
            if pathnameArray[2] == "realtime":
                return realTime.returnLayout(pathnameArray[3])
    return home.layout


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
])


if __name__ == '__main__':
    app.run_server(threaded=True, debug=False)
