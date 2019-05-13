import struct
import threading as th
from _datetime import datetime
import glob
import os
import socket
import time
import numpy as np
from nptdms import TdmsFile
import pandas as pd
import configparser
import random

# Class that loadins raw TDMS files,
# and sendning their calculated mean of values
# over TCP communication


class DataSender(th.Thread):
    def __init__(self, threadID, address, port, pathToData, timeFrom=datetime.fromtimestamp(0)):
        th.Thread.__init__(self)
        self.paused = True
        self.threadID = threadID
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = address
        self.port = port
        self.conn = None
        self.pathToData = pathToData
        self.timeFrom = timeFrom
        self.connected = False
        self.infoFile = configparser.ConfigParser()
        self.sensorName = None
        self.startTime = datetime.now()

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
        self.infoFile.read(self.pathToData + '/info.ini')

        Fs = int(self.infoFile["Sensors"]["FS"]) / 100  # konverzia na 0.1 Hz, aby visiel vysledok pre ms a nie s
        blockSize = int(self.infoFile["Sensors"]["BaseBlockSize"])
        measurementTime = int(self.infoFile["Sensors"]["BaseBlockSize"])/int(self.infoFile["Sensors"]["FS"])
        self.sensorName = self.infoFile['Sensors']['SensorNames'].split(';')[2]  # todo obhajit 2ku index

        while True:
            if not self.connected:
                continue
            else:
                break

        filenames = sorted(glob.glob(self.pathToData + '/*.tdms'))
        dfFilenames = pd.DataFrame({'filenames': filenames})
        dfFilenames['date'] = dfFilenames['filenames'].apply(
            lambda x: datetime.strptime(x[len(x) - 18:len(x) - 5], '%y%m%d_%H%M%S'))
        dfFilenames.sort_values(by='date')
        maskForNewFilesOnly = dfFilenames['date'] > self.timeFrom
        dfFilenames = dfFilenames[maskForNewFilesOnly]
        dfFilenames.reset_index()
        filenames = dfFilenames.filenames

        self.timeFrom = datetime.now()

        while True:
            for filename in filenames:
                while True:
                    if self.paused:
                        continue
                    else:
                        break
                tdmsf = TdmsFile(os.path.join(self.pathToData + '/', filename))

                if self.sensorName not in tdmsf.as_dataframe():
                    continue

                sensorMeasurement = tdmsf.as_dataframe()[self.sensorName].as_matrix().astype(np.float64)
                if np.isnan(sensorMeasurement.sum()):
                    break

                timestamp = int(time.time())

                w = np.int(np.floor(Fs))  # width of the window for computing RMS
                steps = np.int_(np.floor(blockSize / w))  # Number of steps for RMS
                x_RMS = np.zeros((steps, 1))  # Create array for RMS values
                for i in range(0, steps):
                    x_RMS[i] = np.sqrt(np.mean(sensorMeasurement[(i * w):((i + 1) * w)] ** 2))
                value = x_RMS.mean()

                data = struct.pack('!dd', timestamp, value)
                self.socket.send(data)

                time.sleep(measurementTime + random.randint(0, 2) - 0.8)

            filenames = sorted(glob.glob(self.pathToData + '/*.tdms'))
            dfFilenames = pd.DataFrame({'filenames': filenames})
            dfFilenames['date'] = dfFilenames['filenames'].apply(
                lambda x: datetime.strptime(x[len(x) - 18:len(x) - 5], '%y%m%d_%H%M%S'))
            dfFilenames.sort_values(by='date')
            maskForNewFilesOnly = dfFilenames['date'] > self.timeFrom
            dfFilenames = dfFilenames[maskForNewFilesOnly]
            dfFilenames.reset_index()
            filenames = dfFilenames.filenames

            if (datetime.now() - self.startTime).seconds > 30 * 60:
                self.startTime = datetime.now()
                self.timeFrom = datetime.fromtimestamp(0)
                filenames = sorted(glob.glob(self.pathToData + '/*.tdms'))


    def changePausedState(self):
        self.paused = not self.paused

    def isPausedState(self):
        return self.paused

    def stop(self):
        if self.conn:
            self.conn.close()
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()

    def __del__(self):
        self.stop()
