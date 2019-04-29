"""
Producer/Controller Dash Outline
Copyright 2018 Steve Korson
"""
import socket
import time

from dash.dependencies import Output, Event, Input, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import threading as th
import time as t
from device.dataProducer import DataProducerTcpServer
from device.dataSender import DataSender
from app import app


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


controllerObj = None
dataSenderObj = None
layout = html.Div(
    [
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
            id='graph-update',
            interval=500
        ),
        dcc.Interval(
            id='interval-component',
            interval=1 * 1000,  # in milliseconds
            n_intervals=0
        ),
        html.Button('Start Recieveing Data (dataProducer.py paused change)', id='buttonPause'),
        html.Br(),
        html.Button('Start Sending Data (dataSender.py start simulating realtime data)', id='buttonSenderStart'),
        html.Br(),
        html.Button('Reset', id='buttonReset', ),
        html.Div(id="outputDiv", children="Ahoj David")
    ]
)


def returnLayout():
    portNumber = 32005

    dataProducerTcpServerObj = DataProducerTcpServer(1, 'localhost', portNumber)

    global dataSenderObj
    dataSenderObj = DataSender(1, "localhost", portNumber, "/mnt/sda2/Device_A")

    global controllerObj
    controllerObj = DataController(1, dataProducerTcpServerObj, dataSenderObj)

    dataProducerTcpServerObj.start()
    time.sleep(1)
    dataSenderObj.start()
    controllerObj.start()
    return layout


@app.callback(Output('live-graph', 'figure'),
              [Input('interval-component', 'n_intervals')],
              [State('live-graph', 'figure')])
def update_data(n, state):
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
              [Input('buttonReset', 'n_clicks')], )
def send_reset(n_clicks):
    if n_clicks is None:
        return 'Reset (untouched)'
    # Optionally to try and except, you could semaphore protect the calls (with fileIO rather than globals)
    try:
        controllerObj.send_cmd('R')
    except:
        print("Interface is busy. Handle the exception.")
    return 'Reset'


@app.callback(Output('buttonSenderStart', 'children'),
              [Input('buttonSenderStart', 'n_clicks')], )
def sendStartData(n_clicks):
    if n_clicks is None:
        return 'Start Sending Data (dataSender.py start simulating realtime data)'
    dataSenderObj.changePausedState()
    if n_clicks % 2:
        return 'Pause Recieveing Data (dataProducer.py paused change)'
    return 'Start Sending Data (dataSender.py start simulating realtime data)'


@app.callback(Output('buttonPause', 'children'),
              [Input('buttonPause', 'n_clicks')])
def send_pause(n_clicks):
    if n_clicks is None:
        return 'Start Recieveing Data (dataProducer.py paused change)'

    # Optionally to try and except, you could semaphore protect the calls (with fileIO rather than globals)
    print("PAUSE/RESUME BUTTON PRESSED")
    try:
        controllerObj.send_cmd('P')
    except:
        print("Interface is busy. Handle the exception.")
    if n_clicks % 2:
        return 'Pause Recieveing Data (dataProducer.py paused change)'
    return 'Resume Recieveing Data (dataProducer.py paused change)'


if __name__ == '__main__':
    app.run_server(threaded=True, debug=False)

    # dataProducerTcpServerObj.stop()
    # controllerObj.stop()

    # print("Fin.")
