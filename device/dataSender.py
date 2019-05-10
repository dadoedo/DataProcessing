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
import configparser

PATHS_TO_COMPANIES = [
    "/mnt/sda2/Device_A",
    "/mnt/sda2/Device_B",
    "/mnt/sda2/Device_C",
    "/mnt/sda2/Device_D",
]

PATH_TO_DATA = PATHS_TO_COMPANIES[0]

INFO = configparser.ConfigParser()
INFO.read(PATH_TO_DATA + '/info.ini')

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


# Class that simulates sending loading raw TDMS files,
# and sendning their calculated mean of values
# over TCP communication
class DataSender(th.Thread):
    def __init__(self, threadID, address, port, pathToData, sensorName="/'raw'/'1'"):
        print("DATA SENDER ===========  Created...")
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
        self.infoFile = configparser.ConfigParser()

    def connect(self):
        try:
            # self.socket.setblocking(False)
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
        print("DATA SENDER =========== connected, waiting for button start, puased = {}".format(self.paused))

        while True:
            if not self.connected:
                continue
            else:
                break

        print("===========  DataSender: connected, going to send files")
        filenames = sorted(glob.glob(self.pathToData + '/*.tdms'))

        idx = 0
        timestamp = None
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

            sensorMeasurement = tdmsf.as_dataframe()[self.sensorName].as_matrix().astype(np.float64)
            # timestamp = datetime.strptime(filename[len(filename) - 18:len(filename) - 5], '%y%m%d_%H%M%S').timestamp()

            if timestamp is None:
                timestamp = int(time.time())
            else:
                timestamp = timestamp + measurementTime
            value = sensorMeasurement.mean()
            w = np.int(np.floor(Fs))  # width of the window for computing RMS
            steps = np.int_(np.floor(blockSize / w))  # Number of steps for RMS

            x_RMS = np.zeros((steps, 1))  # Create array for RMS values
            for i in range(0, steps):
                x_RMS[i] = np.sqrt(np.mean(sensorMeasurement[(i * w):((i + 1) * w)] ** 2))

            value = x_RMS.mean()
            hasNAN = np.isnan(sensorMeasurement.sum())
            if hasNAN:
                idx += 1
                break
            # print(int(timestamp), value)
            # timestampX = timestamp
            # for index, valueX in enumerate(sensorMeasurment[::100]):
            #     # print(valueX)
            #     data = struct.pack('!dd', timestamp + index, valueX)
            #     self.socket.send(data)
            #     time.sleep(0.1)

            data = struct.pack('!dd', timestamp, value)
            # print("DataSender: sending {} {}".format(int(timestamp), value))
            print("{} sends {}".format(filename, value))
            self.socket.send(data)

            # time.sleep(measurementTime - 0.25)
            time.sleep(0.25)
            idx += 1

    def changePausedState(self):
        self.paused = not self.paused

    def stop(self):
        if self.conn:
            print("------- SENDER stop() called")
            self.conn.close()
            # self.conn.__del__()
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()

    def __del__(self):
        if self.conn:
            print("------- SENDER stop() called")
            self.conn.close()
            # self.conn.__del__()
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()


if __name__ == '__main__':
    filenames = sorted(glob.glob(PATH_TO_DATA + '/*.tdms'))
    FS = int(INFO['Sensors']['FS'])
    baseblocksize = int(INFO['Sensors']['BaseBlockSize'])

    # dataSenderObejct = DataSender("localhost", 32001)
    # dataSenderObejct.connect()
    # dataSenderObejct.run()
