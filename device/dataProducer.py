import copy
import socket
import struct
from datetime import datetime

import dash
from dash.dependencies import Output, Event, Input, State
import dash_core_components as dcc
import dash_html_components as html
import plotly
import random
import plotly.graph_objs as go
from collections import deque
import threading as th
import time as t
import random as rnd
import sys
import numpy as np


class DataProducerTcpServer(th.Thread):
    def __init__(self, threadID, address, port):
        print("DATA PRODUCER ===========  Created...")
        th.Thread.__init__(self)
        self.threadID = threadID
        self.done = False
        self.sleep_time = 0.25
        self.values = []
        self.timestamps = []
        self.pause = True
        self.busy = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = address
        self.port = port
        self.conn = None
        self.addr = None

    def __connect(self):
        # self.socket.setblocking(False)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.ip, self.port))
        print("DATA PRODUCER ===========  Waiting...")
        self.socket.listen(1)
        self.conn, self.addr = self.socket.accept()
        print('DATA PRODUCER ===========  Connected to address: {}'.format(self.addr))

    def run(self):
        print("DATA PRODUCER ===========  done = {}, pause = {}".format(self.done, self.pause))
        self.__connect()
        print('DATA PRODUCER ===========  Going to main loop')
        while not self.done:
            # Main loop
            self.busy = self.__update()
            t.sleep(self.sleep_time)
        # Cleanup

    def __update(self):
        if self.pause:
            # print("DATA PRODUCER --------- PAUSED")
            return True

        receivedBytes = self.conn.recv(8 * 2 * 500)

        unpackString = '!'
        for i in range(0, (len(receivedBytes) // 8)):
            unpackString = unpackString + 'd'

        received = struct.unpack(unpackString, receivedBytes)
        print("PRUDCER RECIEVED = {}".format(received))

        if len(received) is 0:
            return False

        for index, value in enumerate(received):
            if index % 2 == 0:
                self.timestamps.append(datetime.utcfromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S'))
            else:
                self.values.append(value)

        print("PRODUCER STATE = {}".format({
            "values": self.values,
            "timestamps": self.timestamps,
        }))
        t.sleep(self.sleep_time)
        return True

    def getData(self):
        if self.pause:
            return {
                "values": [],
                "timestamps": [],
            }
        values = self.values
        timestamps = self.timestamps
        self.values = []
        self.timestamps = []
        # print("DATA PRODUCER -------------- returning {}".format({'values':values, 'times':timestamps}))
        return {
            "values": values,
            "timestamps": timestamps,
        }

    def pauseData(self, state):
        self.pause = state

    def stop(self):
        if self.conn:
            print("------- PRODUCER stop() called")
            self.conn.close()
            # self.conn.__del__()
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()

    def __del__(self):
        if self.conn:
            print("------- PRODUCER stop() called")
            self.conn.close()
            # self.conn.__del__()
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        self.values = []
        self.timestamps = []
