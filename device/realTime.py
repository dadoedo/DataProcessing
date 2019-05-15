import time
import MySQLdb

from dash.dependencies import Output, Input, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

from realtime.dataReceiver import DataReceiver
from realtime.dataSender import DataSender
from realtime.dataController import DataController

from app import app
from app import configInfo
from app import controllerObjects


conn_get = MySQLdb.connect(host=configInfo["DATABASE"]["host"], user=configInfo["DATABASE"]["username"],
                           passwd=configInfo["DATABASE"]["password"], db=configInfo["DATABASE"]["database"])
cursor = conn_get.cursor()

layout = html.Div(
    [
        dcc.Link('Home', href='/', style={'textAlign': 'right'}),
        dcc.Location(id='url-realtime', refresh=False),
        dcc.Graph(id='live-graph', figure={
            'data': [
                go.Scatter(
                    x=[],
                    y=[],
                )],
            'layout': {
                'title': "Real Time Simulation",
                'yaxis': {
                    'title': 'Amplitude'
                }
            }}),
        dcc.Interval(
            id='interval-component',
            interval=1 * 300,  # in milliseconds
            n_intervals=0
        ),
        html.Button('Start Recieveing Data', id='buttonReciever', style={'margin': '50px'}),
        html.Button('Start Sending Data', id='buttonSender', style={'margin': '50px'}),
        html.Br(),
        dcc.ConfirmDialogProvider(
            children=html.Button('Reset', style={'margin-left': '50px'}),
            id='button-reset-confirm',
            message='All displayed data will be lost'
        ),
        html.Div(id="outputDiv", children="")
    ]
)


def returnLayout(deviceId):
    query = "select name from device where id = \"{}\"".format(deviceId)
    cursor.execute(query)
    deviceName = cursor.fetchone()
    if not deviceName:
        return html.Div("Bad Link!")
    deviceName = deviceName[0]
    time.sleep(1)

    controllerObj = next(item for item in controllerObjects if item["id"] == int(deviceId))['object']

    if controllerObj is not None:
        return layout

    portNumber = 32015 + int(deviceId)

    dataRecieverObj = DataReceiver(1, 'localhost', portNumber)
    dataSenderObj = DataSender(1, "localhost", portNumber,str(configInfo["PATH"]["pathToDevices"] + deviceName))

    controllerObj = DataController(1, dataRecieverObj, dataSenderObj, deviceName)

    dataRecieverObj.start()
    time.sleep(0.25)
    dataSenderObj.start()
    controllerObj.start()

    next(item for item in controllerObjects if item["id"] == int(deviceId))['object'] = controllerObj

    return layout


@app.callback(Output('live-graph', 'figure'),
              [Input('interval-component', 'n_intervals'),
               Input('url-realtime', 'pathname')],
              [State('live-graph', 'figure')])
def update_data(n, pathname, state):
    if "realtime" not in pathname:
        return
    deviceId = int(pathname[-1])
    controllerObj = next(item for item in controllerObjects if item["id"] == deviceId)['object']
    deviceName = ''
    if controllerObj is not None:
        data = controllerObj.getData()
        deviceName = controllerObj.deviceName
    else:
        data = {'timestamps': [], 'values': []}
    if state is None:
        return {
            'data': [
                go.Scatter(
                    x=[],
                    y=[],
                )],
            'layout': {
                'title': "Real Time Simulation - {}".format(deviceName),
                'yaxis': {
                    'title': 'Amplitude'
                }
            }
        }
    return {
        'data': [{
            'x': (state["data"][0]["x"]) + data['timestamps'],
            'y': (state["data"][0]["y"]) + data["values"],
        }],
        'layout': {'uirevision': 'static',
                   'title': "Real Time Simulation - {}".format(deviceName),
                   'yaxis': {
                       'title': 'Amplitude'
                   }
                   }
    }


# @app.callback(Output('url', 'pathname'),
#               [Input('button-reset-confirm', 'submit_n_clicks'),
#                Input('url-realtime', 'pathname')
#                ])
# def sendReset(n_clicks, pathname):
#     if n_clicks is None:
#         return
#     deviceId = int(pathname[-1])
#     controllerObj = next(item for item in controllerObjects if item["id"] == deviceId)['object']
#     # try:
#     controllerObj.send_cmd('X')
#     deviceName = controllerObj.deviceName
#     # except:print("Interface is busy. Handle the exception.")
#     print('pathname')
#     return pathname


@app.callback(Output('buttonSender', 'children'),
              [Input('buttonSender', 'n_clicks'),
               Input('url-realtime', 'pathname')], )
def sendStartData(n_clicks, pathname):
    if "realtime" not in pathname:
        return
    deviceId = int(pathname[-1])
    controllerObj = next(item for item in controllerObjects if item["id"] == deviceId)['object']

    if n_clicks is None:
        if controllerObj.senderObj.isPausedState():
            return 'Start Data Sending'
        return 'Pause Data Sending'
    wasPaused = controllerObj.senderObj.isPausedState()
    try:
        controllerObj.send_cmd('S')
    except:
        print("Interface is busy. Handle the exception.")
    if wasPaused:
        return 'Pause Data Sending'
    return 'Start Data Sending'


@app.callback(Output('buttonReciever', 'children'),
              [Input('buttonReciever', 'n_clicks'),
               Input('url-realtime', 'pathname')])
def send_pause(n_clicks, pathname):
    if "realtime" not in pathname:
        return
    deviceId = int(pathname[-1])
    controllerObj = next(item for item in controllerObjects if item["id"] == deviceId)['object']
    if n_clicks is None:
        if controllerObj.recieverObj.isPausedState():
            return 'Start Receiving Data'
        return 'Pause Receiving Data'
    wasPaused = controllerObj.recieverObj.isPausedState()
    try:
        controllerObj.send_cmd('R')
    except:
        print("Interface is busy. Handle the exception.")
    if wasPaused:
        return 'Pause Receiving Data'
    return 'Start Receiving Data'
