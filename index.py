import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import home
from app import app
from tdms import tdms, mat
from device import history, realTime
from batch import processing
from apscheduler.schedulers.blocking import BlockingScheduler


sched = BlockingScheduler()

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
                return realTime.returnLayout(pathnameArray[3])
    if pathname == '/visualisation/tdms':
        return tdms.layout
    elif pathname == '/visualisation/mat':
        return mat.layout
    elif pathname == '/visualisation/4dot':
        return history.layout
    else:
        return home.layout


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
])


# Runs as cron job every day at 3AM in the morning
# Calls batch processing
@sched.scheduled_job('cron', day_of_week='mon-sun', hour=3)
def scheduledBatchProcessing():
    processing.processBatches()


if __name__ == '__main__':
    app.run_server(threaded=True, debug=False)
    sched.start()
