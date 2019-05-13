import socket
import struct
from datetime import datetime

import threading as th
import time as t


class DataReceiver(th.Thread):
    def __init__(self, threadID, address, port):
        th.Thread.__init__(self)
        self.threadID = threadID
        self.done = False
        self.sleep_time = 0.25
        self.values = []
        self.timestamps = []
        self.lastDataCallbackTime = None
        self.paused = True
        self.busy = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = address
        self.port = port
        self.conn = None
        self.addr = None

    def __connect(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.ip, self.port))
        self.socket.listen(1)
        self.conn, self.addr = self.socket.accept()

    def run(self):
        self.__connect()
        while not self.done:
            self.busy = self.__update()
            t.sleep(self.sleep_time)

    def __update(self):
        if self.paused:
            return True

        receivedBytes = self.conn.recv(8 * 2 * 500)

        unpackString = '!'
        for i in range(0, (len(receivedBytes) // 8)):
            unpackString = unpackString + 'd'

        received = struct.unpack(unpackString, receivedBytes)

        if len(received) is 0:
            return False

        for index, value in enumerate(received):
            if index % 2 == 0:
                self.timestamps.append(datetime.utcfromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S'))
            else:
                self.values.append(value)

        if self.lastDataCallbackTime is not None:
            if (datetime.now() - self.lastDataCallbackTime).seconds > 60 * 5:
                self.values = []
                self.timestamps = []
                self.changePausedState()
                # Delete the 3 Objects ?

        t.sleep(self.sleep_time)
        return True

    def getData(self):
        if self.paused:
            return {
                "values": [],
                "timestamps": [],
            }
        self.lastDataCallbackTime = datetime.now()
        values = self.values
        timestamps = self.timestamps
        self.values = []
        self.timestamps = []
        return {
            "values": values,
            "timestamps": timestamps,
        }

    def changePausedState(self):
        self.paused = not self.paused

    def isPausedState(self):
        return self.paused

    def resetData(self):
        self.values = []
        self.timestamps = []
        self.lastDataCallbackTime = None

    def stop(self):
        if self.conn:
            self.conn.close()
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()

    def __del__(self):
        self.stop()
        self.values = []
        self.timestamps = []
