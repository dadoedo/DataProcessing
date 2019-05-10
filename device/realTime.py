"""
Producer/Controller Dash Outline
Copyright 2018 Steve Korson
"""
import time

import weakref
import MySQLdb
from dash.dependencies import Output, Event, Input, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import threading as th
import time as t
from device.dataProducer import DataProducerTcpServer
from device.dataSender import DataSender
from app import app
from app import configInfo
from app import dataProducerTcpServerObjects, dataSenderObjects, controllerObjects

conn_get = MySQLdb.connect(host=configInfo["DATABASE"]["host"], user=configInfo["DATABASE"]["username"],
                           passwd=configInfo["DATABASE"]["password"], db=configInfo["DATABASE"]["database"])
cursor = conn_get.cursor()


class DataController(th.Thread):
    def __init__(self, threadID, producerObj, senderObj):
        # Passing in producer target here for demo
        # Typical system has controller and producer connected external
        th.Thread.__init__(self)
        self.threadID = threadID
        self.done = False
        self.producerObj = producerObj
        self.senderObj = senderObj
        self.sleep_time = 0.250
        self.busy = False
        self.__cmd = None
        self.__newCmd = False
        self.fakeRspTime = 0
        self.paused = True

    def stop(self):
        self.done = True

    def run(self):
        while not self.done:
            # Main loop
            if self.__newCmd:
                self.__newCmd = False
                self.__procCmd()
            if self.busy:
                # self.busy = self.__check_for_rsp(timeout=0.250)
                self.busy = False
            t.sleep(self.sleep_time)
        # Cleanup

    def getData(self):
        return self.producerObj.getData()

    def send_cmd(self, cmd):
        """
            Method used by callers to send commands to the command interface
        """
        if not self.busy:
            self.busy = True
            self.__newCmd = True
            self.__cmd = cmd
            return True
        else:
            raise UserWarning("Command interpreter is busy.")

    def __procCmd(self):
        """
        Emulate sending a commnd out a socket or other IPC
        """
        # -----------------------------
        self.busy = True
        if self.__cmd == 'P':  # Pause
            if self.paused:
                self.paused = False
            else:
                self.paused = True
            self.producerObj.pauseData(self.paused)

        if self.__cmd == 'R':
            self.senderObj.pauseData()
        # -----------------------------

    def __check_for_rsp(self, timeout):
        """
            Once command is sent out the interface, await a response (or timeout)
        """
        t.sleep(timeout)

        # For now emulate checking for a response
        # ---------------------------------
        # This can take a random amount of loops (not time really)
        # before setting a non-busy result.
        # ---------------------------------

    def deleteSenderProducer(self):
        self.producerObj.__del__()
        self.senderObj.__del__()

        print("----- controller deleted producer and sender")


# controllerObjects = []
# dataSenderObjects = []
# dataProducerTcpServerObjects = []
# cursor.execute("SELECT id FROM device")
# for row in cursor.fetchall():
#     deviceId = row[0]
#     controllerObjects.append({"id": deviceId, "object": None})
#     dataSenderObjects.append({"id": deviceId, "object": None})

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
            interval=1 * 100,  # in milliseconds
            n_intervals=0
        ),
        dcc.ConfirmDialog(
            id='confirm',
            message='Danger danger! Are you sure you want to continue?',
        ),
        html.Button('Start Recieveing Data (dataProducer.py paused change)', id='buttonPause'),
        html.Br(),
        html.Button('Start Sending Data (dataSender.py start simulating realtime data)', id='buttonSenderStart'),
        html.Br(),
        html.Button('Reset', id='buttonReset', ),
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
    # global dataSenderObjects
    # global controllerObjects

    print(dataSenderObjects)
    print(controllerObjects)
    print(deviceId)

    dataSenderObj = next(item for item in dataSenderObjects if item["id"] == int(deviceId))['object']
    controllerObj = next(item for item in controllerObjects if item["id"] == int(deviceId))['object']
    print(dataSenderObj)
    print("dataSenderOBJ is none = {}".format(dataSenderObj is None))

    if dataSenderObj is not None and controllerObj is not None:
        # controllerObj.deleteSenderProducer()
        # print("dataSenderOBJ is none = {}".format(dataSenderObj is None))

        return layout
        time.sleep(1)

    portNumber = 32009 + int(deviceId)
    # time.sleep(3)
    # global dataProducerTcpServerObjects

    dataProducerTcpServerObj = next((item for item in dataProducerTcpServerObjects if item["id"] == deviceId), None)
    if dataProducerTcpServerObj is None:
        dataProducerTcpServerObj = DataProducerTcpServer(1, 'localhost', portNumber)
        dataSenderObj = DataSender(1, "localhost", portNumber, configInfo["PATH"]["pathToDevices"] + deviceName)

        controllerObj = DataController(1, dataProducerTcpServerObj, dataSenderObj)

        dataProducerTcpServerObj.start()
        time.sleep(1)
        dataSenderObj.start()

        controllerObj.start()
        next(item for item in dataSenderObjects if item["id"] == int(deviceId))['object'] = dataSenderObj
        next(item for item in controllerObjects if item["id"] == int(deviceId))['object'] = controllerObj
        dataProducerTcpServerObjects.append({'id' : deviceId, 'object': dataProducerTcpServerObj})

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

    if controllerObj is not None:
        data = controllerObj.getData()
    else:
        data = {'timestamps': [], 'values': []}
    # print("requesting data for graph {}".format(data))
    if state is None:
        return {
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
            }
        }
    return {
        'data': [{
            'x': (state["data"][0]["x"]) + data['timestamps'],
            'y': (state["data"][0]["y"]) + data["values"],
        }],
        'layout': {'uirevision': 'static',
                   'title': "Real Time Simulation",
                   'yaxis': {
                       'title': 'Amplitude'
                   }
                   }
    }


@app.callback(Output('buttonReset', 'children'),
              [Input('buttonReset', 'n_clicks'),
               Input('url-realtime', 'pathname')])
def send_reset(n_clicks, pathname):

    if n_clicks is None:
        return 'Reset (untouched)'
    # Optionally to try and except, you could semaphore protect the calls (with fileIO rather than globals)
    deviceId = int(pathname[-1])
    controllerObj = next(item for item in controllerObjects if item["id"] == deviceId)['object']
    print("send_reset")
    print(controllerObjects)
    try:
        controllerObj.send_cmd('R')
    except:
        print("Interface is busy. Handle the exception.")
    return 'Reset'


@app.callback(Output('buttonSenderStart', 'children'),
              [Input('buttonSenderStart', 'n_clicks'),
               Input('url-realtime', 'pathname')], )
def sendStartData(n_clicks, pathname):
    if "realtime" not in pathname:
        return
    if n_clicks is None:
        return 'Start Sending Data (dataSender.py)'
    print("sendStarrtData")
    print(controllerObjects)
    deviceId = int(pathname[-1])
    dataSenderObj = next(item for item in dataSenderObjects if item["id"] == deviceId)['object']
    dataSenderObj.changePausedState()
    if n_clicks % 2:
        return 'Pause Sending Data (dataSender.py)'
    return 'Resume Sending Data (dataSender.py)'


@app.callback(Output('buttonPause', 'children'),
              [Input('buttonPause', 'n_clicks'),
               Input('url-realtime', 'pathname')])
def send_pause(n_clicks, pathname):
    if "realtime" not in pathname:
        return
    if n_clicks is None:
        return 'Start Recieveing Data (dataProducer.py)'

    # Optionally to try and except, you could semaphore protect the calls (with fileIO rather than globals)
    deviceId = int(pathname[-1])
    print("send_pause")
    print(controllerObjects)
    controllerObj = next(item for item in controllerObjects if item["id"] == deviceId)['object']
    try:
        controllerObj.send_cmd('P')
    except:
        print("Interface is busy. Handle the exception.")
    if n_clicks % 2:
        return 'Pause Recieveing Data (dataProducer.py)'
    return 'Resume Recieveing Data (dataProducer.py)'
