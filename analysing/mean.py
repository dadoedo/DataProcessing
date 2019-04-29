import dash_core_components as dcc
import dash_html_components as html
import MySQLdb
import configparser
from _datetime import datetime
import glob
import os
import numpy as np
from nptdms import TdmsFile
from tqdm import tqdm


conn_get = MySQLdb.connect(host="172.16.23.204", user="fourdot", passwd="4d0tFourdot", db="dp")
cursor = conn_get.cursor()


MEAN_AVERAGE_TYPE = 1
PATHS_TO_DEVICES = "/home/david/HDD/"
DEVICES = [
    "Device_A",
    "Device_B",
    "Device_C",
]

PATH_TO_DATA = PATHS_TO_DEVICES + DEVICES[1]

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


def sendData(plottedSensor, filenames, plotID):

    # nie kazdy TDMS subor ma kazdy sensor
    idx = 0
    # pbar = tqdm(total=len(filenames))

    for filename in filenames:
        # pbar.set_description(f'Processing {filename}')

        tdmsf = TdmsFile(os.path.join(PATH_TO_DATA + '/', filename))

        if plottedSensor not in tdmsf.as_dataframe():
            # pbar.update(1)
            idx = idx + 1
            continue

        sensorMeasurement = tdmsf.as_dataframe()[plottedSensor].as_matrix().astype(np.float64)

        timestamp = datetime.strptime(filename[len(filename) - 18:len(filename) - 5], '%y%m%d_%H%M%S').timestamp()
        mean = sensorMeasurement.mean()

        hasNAN = np.isnan(sensorMeasurement.sum())

        if hasNAN:
            idx += 1
            break

        entry = "INSERT INTO data_entry VALUES ({}, {}, {}, {})".format(timestamp, mean, MEAN_AVERAGE_TYPE, plotID)
        cursor.execute(entry)

        idx += 1
        # pbar.update(1)

    conn_get.commit()


if __name__ == '__main__':
    filenames = glob.glob(PATH_TO_DATA + '/*.tdms')
    FS = int(INFO['Sensors']['FS'])
    baseblocksize = int(INFO['Sensors']['BaseBlockSize'])
    for i in range(len(Sensors)):
        query = "select id from plot where device = \"{}\" and sensor = \"{}\" ".format(DEVICES[1], Sensorlabels[i])
        cursor.execute(query)
        rows = cursor.fetchall()
        plotID = rows[0][0]
        sendData(Sensors[i], filenames, plotID)

    print("Done.")
    exit(0)


