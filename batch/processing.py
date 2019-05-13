import configparser
import glob
import os
import threading

import MySQLdb
import numpy as np
import pandas as pd
from _datetime import datetime
from nptdms import TdmsFile
from scipy import stats
from tqdm import tqdm

MEAN_AVERAGE_TYPE = 1
RMS_TYPE = 2
VARIANCE_TYPE = 3
SKEWNESS_TYPE = 4
COMPANY_TYPE = 10

NO_OF_THREADS = 3

typeToHeadings = {
    MEAN_AVERAGE_TYPE: 'Mean average value',
    RMS_TYPE: 'Effective value - RMS [FS / 100]',
    VARIANCE_TYPE: 'Variance',
    SKEWNESS_TYPE: 'Skewness',
    COMPANY_TYPE: 'Partnered company\'s reference processed data',
}


def computeFeatureExtractions(deviceName, filenames, sensorExtractionTypesInfo, infoFile, threadID):
    configInfo = configparser.ConfigParser()
    configInfo.read('../config.ini')
    conn_get = MySQLdb.connect(host=configInfo["DATABASE"]["host"], user=configInfo["DATABASE"]["username"],
                               passwd=configInfo["DATABASE"]["password"], db=configInfo["DATABASE"]["database"])
    cursor = conn_get.cursor()

    idx = 0
    pbar = tqdm(total=len(filenames))
    query = "INSERT INTO data_entry VALUES " + "\n"
    valuesQuery = ""

    if len(sensorExtractionTypesInfo) is 0:
        return
    print(sensorExtractionTypesInfo)
    timestamp = 0
    plot_setID = 0

    for filename in filenames:
        pbar.set_description(f' THREAD {threadID} -- {deviceName} -- Processing {filename}')

        tdmsf = TdmsFile(os.path.join(configInfo['PATH']['pathToDevices'] + deviceName + '/', filename))

        for sensorExtractionTypes in sensorExtractionTypesInfo:
            plot_setID = sensorExtractionTypes[0]
            plottedSensor = sensorExtractionTypes[1]
            extractionTypes = sensorExtractionTypes[2]

            if len(extractionTypes) is 0:
                continue

            if plottedSensor not in tdmsf.as_dataframe():
                print("Plotted Sensor is not in dataframe, going to next")
                continue

            sensorMeasurement = tdmsf.as_dataframe()[plottedSensor].as_matrix().astype(np.float64)

            timestamp = datetime.strptime(filename[len(filename) - 18:len(filename) - 5], '%y%m%d_%H%M%S').timestamp()

            hasNAN = np.isnan(sensorMeasurement.sum())

            if hasNAN:
                print("Plotted Sensor has NaN, going to next")
                continue

            if MEAN_AVERAGE_TYPE in extractionTypes:
                mean = sensorMeasurement.mean()
                valuesQuery = valuesQuery + "({}, {}, {}, {}),\n".format(timestamp, mean, MEAN_AVERAGE_TYPE, plot_setID)

            if SKEWNESS_TYPE in extractionTypes:
                skewness = stats.skew(sensorMeasurement)
                valuesQuery = valuesQuery + "({}, {}, {}, {}),\n".format(timestamp, skewness, SKEWNESS_TYPE, plot_setID)

            if VARIANCE_TYPE in extractionTypes:
                variance = np.var(sensorMeasurement).mean()
                valuesQuery = valuesQuery + "({}, {}, {}, {}),\n".format(timestamp, variance, VARIANCE_TYPE, plot_setID)

            if RMS_TYPE in extractionTypes:
                Fs = int(infoFile["Sensors"]["FS"]) / 100  # konverzia na Hz * 0.01, aby visiel vysledok pre ms a nie s
                blockSize = int(infoFile["Sensors"]["BaseBlockSize"])
                w = np.int(np.floor(Fs))  # width of the window for computing RMS
                steps = np.int_(np.floor(blockSize / w))  # Number of steps for RMS
                x_RMS = np.zeros((steps, 1))  # Create array for RMS values
                for i in range(0, steps):
                    x_RMS[i] = np.sqrt(np.mean(sensorMeasurement[(i * w):((i + 1) * w)] ** 2))
                rms = x_RMS.mean()
                valuesQuery = valuesQuery + "({}, {}, {}, {}),\n".format(timestamp, rms, RMS_TYPE, plot_setID)

            # Here would be placed another processing method, If I had one
                # e.g. The partner company could call their algorithms

        idx += 1
        pbar.update(1)

    print(query)
    if valuesQuery is "":
        return

    query = query + valuesQuery
    query = query[:-2]

    cursor.execute(query)
    conn_get.commit()

    if plot_setID is not 0:
        query = "UPDATE plot_set SET last_processed_time = {} WHERE id = {}".format(plot_setID, timestamp)
        print(query)
        cursor.execute(query)
        conn_get.commit()


def processBatches():
    configInfo = configparser.ConfigParser()
    configInfo.read('../config.ini')

    conn_get = MySQLdb.connect(host=configInfo["DATABASE"]["host"], user=configInfo["DATABASE"]["username"],
                               passwd=configInfo["DATABASE"]["password"], db=configInfo["DATABASE"]["database"])
    cursor = conn_get.cursor()

    devices = pd.read_sql("Select * from device", conn_get)
    for device in devices.itertuples():
        print(device.name)
        INFO = configparser.ConfigParser()
        INFO.read(configInfo['PATH']['pathToDevices'] + str(device.name) + '/info.ini')

        sensorExtractionTypesInfo = []

        lastTimeOfProcessing = 0

        for sensorName, sensorLabel in zip(INFO['Sensors']['SensorNames'].split(';'),
                                           INFO['Sensors']['SensorLabels'].split(';')):
            plot_setId = None
            if sensorName is "" or sensorLabel is "":
                continue
            query = "select id, last_processed_time from plot_set where device_id = \"{}\" and sensor = \"{}\" ".format(
                device.id,
                sensorLabel)
            cursor.execute(query)
            rows = cursor.fetchall()
            if len(rows) is 0:
                query = "INSERT INTO plot_set (device_id, sensor, last_processed_time) VALUES ({}, \"{}\")".format(
                    device.id, sensorLabel, 0)
                cursor.execute(query)
                plot_setId = cursor.lastrowid
                conn_get.commit()

            if plot_setId is None:
                plot_setId = rows[0][0]
                lastTimeOfProcessing = rows[0][1]

            extractionTypes = []
            query = "select distinct type from data_entry where plot_set_id = \"{}\" and timestamp > {}".format(
                plot_setId, lastTimeOfProcessing)
            cursor.execute(query)
            rows = cursor.fetchall()
            for row in rows:
                extractionTypes.append(row[0])

            nonComputedTypes = list({1, 2, 3, 4} - set(extractionTypes))
            if len(nonComputedTypes) is not 0:
                sensorExtractionTypesInfo.append([plot_setId, sensorName, nonComputedTypes])

        filenames = glob.glob(configInfo['PATH']['pathToDevices'] + str(device.name) + '/*.tdms')

        dfFilenames = pd.DataFrame({'filenames': filenames})
        dfFilenames['date'] = dfFilenames['filenames'].apply(
            lambda x: datetime.strptime(x[len(x) - 18:len(x) - 5], '%y%m%d_%H%M%S'))

        dfFilenames.sort_values(by='date')

        lastTimeOfProcessing = datetime.fromtimestamp(lastTimeOfProcessing)

        maskForNewFilesOnly = dfFilenames['date'] > lastTimeOfProcessing
        dfFilenames = dfFilenames[maskForNewFilesOnly]
        dfFilenames.reset_index()

        filenames = dfFilenames.filenames

        threads = []

        filenameSplits = np.array_split(np.asarray(filenames), NO_OF_THREADS)
        for index, filenamesSplit in enumerate(filenameSplits):
            t = threading.Thread(target=computeFeatureExtractions,
                                 args=(device.name, filenamesSplit,
                                       sensorExtractionTypesInfo, INFO, index))
            threads.append(t)
            t.start()

        for thread in threads:
            thread.join()

    print("Done.")
    exit(0)


if __name__ == '__main__':
    processBatches()
