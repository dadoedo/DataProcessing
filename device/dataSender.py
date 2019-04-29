import configparser
import asyncio
import struct

import threading as th
from _datetime import datetime
import glob
import os
import pickle
import socket
import time
import numpy as np
from nptdms import TdmsFile
import pandas as pd
from tqdm import tqdm

PATHS_TO_COMPANIES = [
    "/mnt/sda2/Device_A",
    "/mnt/sda2/Device_B",
    "/mnt/sda2/Device_C",
    # "/home/david/HDD/Device_C",
]

PATH_TO_DATA = PATHS_TO_COMPANIES[0]

INFO = configparser.ConfigParser()
INFO.read(PATH_TO_DATA + '/info.ini')
DPI = 500

Sensors = INFO['Sensors']['SensorNames'].split(';')
Sensorlabels = []
for sensor in Sensors:
    sensorName = sensor.replace('\'', '')
    sensorName = sensorName.replace('/', '_')
    sensorName = sensorName.replace(' ', '_')
    Sensorlabels.append(sensorName)

NumOfFilesForSensor = INFO['Sensors']['NumOfFilesForSensor'].split(';')
HOST = 'localhost'
PORT = 32001


class DataSender(th.Thread):
    def __init__(self, threadID, address, port, pathToData, sensorName="/'raw'/'1'"):
        th.Thread.__init__(self)
        self.paused = True
        self.threadID = threadID
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = address
        self.port = port
        self.conn = None
        self.pathToData = pathToData
        self.sensorName = sensorName
        self.connected = False

    def connect(self):
        try:
            self.socket.connect((self.ip, self.port))
            self.connected = True
        except socket.error as exc:
            print("Caught exception socket.error : %s" % exc)
            return False
        return True

    def run(self):
        self.connect()
        print("DATA SENDER =========== connected, waiting for button start, puased = {}".format(self.paused))

        while True:
            if not self.connected:
                continue
            else:
                break

        print("===========  DataSender: connected, going to send files")
        filenames = sorted(glob.glob(self.pathToData + '/*.tdms'))

        idx = 0
        for filename in filenames:

            while True:
                if self.paused:
                    continue
                else:
                    break
            tdmsf = TdmsFile(os.path.join(PATH_TO_DATA + '/', filename))

            # ak subor nema meranie pre sensor
            if self.sensorName not in tdmsf.as_dataframe():
                # pbar.update(1)
                continue

            sensorMeasurment = tdmsf.as_dataframe()[self.sensorName].as_matrix().astype(np.float64)
            # timestamp = datetime.strptime(filename[len(filename) - 18:len(filename) - 5], '%y%m%d_%H%M%S').timestamp()
            timestamp = int(time.time())
            value = sensorMeasurment.mean()
            hasNAN = np.isnan(sensorMeasurment.sum())
            if hasNAN:
                idx += 1
                break
            print(int(timestamp), value)

            data = struct.pack('!dd', timestamp, value)
            print("DataSender: sending {} {}".format(int(timestamp), value))
            self.socket.send(data)

            time.sleep(1.25)
            idx += 1

    def changePausedState(self):
        self.paused = not self.paused


if __name__ == '__main__':
    filenames = sorted(glob.glob(PATH_TO_DATA + '/*.tdms'))
    FS = int(INFO['Sensors']['FS'])
    baseblocksize = int(INFO['Sensors']['BaseBlockSize'])

    # dataSenderObejct = DataSender("localhost", 32001)
    # dataSenderObejct.connect()
    # dataSenderObejct.run()
