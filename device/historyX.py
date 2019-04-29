import glob
import os
import sys
import time

import MySQLdb

from datetime import datetime
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from tqdm import tqdm
import configparser
import pprint
import matplotlib.pyplot as plt
import numpy as np
from nptdms import TdmsFile
import threading

PATHS_TO_COMPANIES = [
    "/home/david/HDD/Company_D_2017",
    "/home/david/HDD/Company_D",
    "/home/david/HDD/Company_E",
    "/home/david/HDD/Company_F"
]

PATH_TO_DATA = PATHS_TO_COMPANIES[2]

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
NumOfFilesForSensor = [718, 718, 718]

analyses = {  # Analysis ID, Device ID
    "ZKL Hlava 3": [408, 11],
    "ZKL Hlava 4": [409, 11],
    "ZKL Hlava 5": [410, 11],
    "PSL 0": [11, 2],
    "PSL 1": [14, 2],
    "PSL 3": [15, 2],
    "PSL 4": [16, 2],
}

thresholds = {
    "off": 0,
    "on": 0.1,
    "risk": 0.5,
}


def return_structure():
    return {
        "off": {
            "data": [],
            "timestamps": [],
            "color": 'rgb(3, 12, 220)',
            "name": "Not Working",
        },
        "on": {
            "data": [],
            "timestamps": [],
            "color": 'rgb(0, 220, 24)',
            "name": "Working",
        },
        "risk": {
            "data": [],
            "timestamps": [],
            "color": 'rgb(205, 12, 24)',
            "name": "Working at Risk",
        },
    }


graphs = []

for name, ids in analyses.items():
    data = return_structure()
    scatters = []
    conn_get = MySQLdb.connect(host="172.16.23.204", user="fourdot", passwd="4d0tFourdot", db="dat_{}".format(ids[1]))
    cursor = conn_get.cursor()
    sql_query = "SELECT time,value FROM analysis_state " \
                "INNER JOIN analysis_value ON analysis_state.id = analysis_value.analysis_state_id " \
                "WHERE (analysis_id = {}) ORDER BY time".format(ids[0])
    cursor.execute(sql_query)
    rows = cursor.fetchall()
    last_whereto = ""
    whereto = ""
    for row in rows:
        if row[1] < thresholds["on"]:
            whereto = "off"
        elif row[1] < thresholds["risk"]:
            whereto = "on"
        else:
            whereto = "risk"
        if last_whereto != whereto:
            data[whereto]["timestamps"].append(datetime.utcfromtimestamp(row[0] - 1).strftime('%Y-%m-%d %H:%M:%S'))
            data[whereto]["data"].append('none')

        last_whereto = whereto

        data[whereto]["timestamps"].append(datetime.utcfromtimestamp(row[0]).strftime('%Y-%m-%d %H:%M:%S'))
        data[whereto]["data"].append(row[1])

    for key, scatter in data.items():
        scatters.append(go.Scatter(
            x=scatter["timestamps"],
            y=scatter["data"],
            name=scatter["name"],
            line=dict(
                color=scatter["color"],
            ),

        ))

    graphs.append(dcc.Graph(
        figure={
            'data': scatters,
            'layout': {
                'title': name,
                'yaxis': {
                    'title': 'Amplitude'
                }
            }
        }
    ))

layout = html.Div(children=[
    html.H2(
        children='4dot data',
        style={
            'textAlign': 'center',
        }
    ),
    dcc.Link('Home', href='/', style={'textAlign': 'right'}),
    html.Div(
        id='output-mat-graphs',
        children=graphs
    ),
])


def worker(sensorn, files, to_freqs, from_freqs, FS, baseblocksize, datapath, cwd, downsample_factor=1):
    datablocksize = baseblocksize // downsample_factor
    num_of_freqs = datablocksize // 2 + 1

    plottedSensor = Sensors[sensorn]
    spectrogram = np.zeros((int(NumOfFilesForSensor[sensorn]), to_freqs - from_freqs))
    freqs = np.fft.fftfreq(datablocksize, 1 / FS)
    freqs = freqs[from_freqs:to_freqs]
    pbar = tqdm(total=len(files))

    hasNAN = False

    xAxis = []
    yAxis = []

    # nie kazdy TDMS subor ma kazdy sensor
    idx = 0
    for file in files:
        tdmsf = TdmsFile(os.path.join(datapath, file))

        pbar.set_description(f'Processing {file}')

        # ak subor nema meranie pre sensor
        if plottedSensor not in tdmsf.as_dataframe():
            pbar.update(1)
            continue

        signal_measurement = tdmsf.as_dataframe()[plottedSensor].as_matrix().astype(np.float64)

        xAxis.append(datetime.strptime(file[len(file) - 18:len(file) - 5], '%y%m%d_%H%M%S'))
        yAxis.append(signal_measurement.mean())
        # pprint.pprint(signal_measurement.mean())
        # pbar.update(1)
        # continue
        hasNAN = np.isnan(signal_measurement.sum())

        if hasNAN:
            break

        if downsample_factor > 1:
            signal_measurement = signal_measurement.reshape(-1, downsample_factor).mean(axis=1)

        if signal_measurement.shape[0] != datablocksize:
            print("Detected inconsistent block size at index {},{} != {}!".format(idx, signal_measurement.shape[0],
                                                                                  datablocksize), file=sys.stderr, )
            exit()

        # apply hamming window to reduce noise in FT
        signal_measurement *= np.hamming(signal_measurement.shape[0])
        spectrum = np.fft.fft(signal_measurement, axis=0)[:num_of_freqs]
        spectrum = spectrum[from_freqs:to_freqs]

        spectrum_magnitude = np.absolute(spectrum)
        spectrogram[idx] = spectrum_magnitude

        pbar.update(1)
        idx += 1

    if hasNAN:
        return
    # maxx = max(yAxis)
    # for i in range(len(yAxis)):
    #     yAxis[i] = (yAxis[i] / maxx) * 2.0
    # plt.plot(yAxis)
    # plt.show()
    # exit(0)
    print("")
    spectrogram = np.transpose(spectrogram)
    os.chdir(cwd)
    title = "{} - {} - custom spectrum".format(Sensors[sensorn], len(files))

    plt.cla()
    plt.suptitle(title, fontsize=16)
    pcm = plt.pcolormesh(range(spectrogram.shape[1] + 1), freqs, spectrogram, vmin=spectrogram.min(),
                         vmax=spectrogram.max(), cmap='plasma')
    cb = plt.colorbar(pcm, extend='max')
    plt.savefig(os.path.join('images', f'{from_freqs}_TO_{to_freqs}{Sensorlabels[sensorn]}_custom.png'),
                dpi=DPI)
    cb.remove()
    plt.cla()

    plt.suptitle(title, fontsize=16)
    spectrogram = np.log10(spectrogram + 1e-15)
    pcm = plt.pcolormesh(range(spectrogram.shape[1] + 1), freqs, spectrogram, vmin=spectrogram.min(),
                         vmax=spectrogram.max(), cmap='plasma')
    cb = plt.colorbar(pcm, extend='max')
    plt.savefig(os.path.join('images', f'{from_freqs}_TO_{to_freqs}{Sensorlabels[sensorn]}_custom_log.png'),
                dpi=DPI)
    cb.remove()
    plt.cla()

    os.chdir(datapath)


def getNumberOfFilesForSensor(filenames):
    result = dict()
    pbar = tqdm(total=len(filenames))

    for filename in filenames:
        tdmsf = TdmsFile(os.path.join(PATH_TO_DATA, filename))
        pbar.set_description(f'Processing {filename}')
        for group in tdmsf.groups():
            for channel in tdmsf.group_channels(group):
                if len(channel.data) < 5:
                    continue
                if ('unit_string' in channel.properties) and channel.property('unit_string') == 'RAW':
                    if channel.path in result:
                        if len(channel.data) in result[channel.path]:
                            result[channel.path][len(channel.data)] += 1
                        else:
                            result[channel.path][len(channel.data)] = 1
                    else:
                        result[channel.path] = {len(channel.data): 1}
        pbar.update(1)

    result_numbers = []
    for sensorname, value in result.items():
        for key, value_2 in value.items():
            result_numbers.append(value_2)
    print(result_numbers)
    return result_numbers


def analyzeSpectrumCustom(datapath, prefix, downsample_factor=1):
    cwd = os.getcwd()
    os.chdir(datapath)

    files = getFilenamesFromTimeToTime(PATH_TO_DATA, "2015-09-28", "2015-09-30")

    FS = int(INFO['Sensors']['FS'])
    baseblocksize = int(INFO['Sensors']['BaseBlockSize'])

    ###
    # global NumOfFilesForSensor
    # NumOfFilesForSensor = getNumberOfFilesForSensor(files)
    #####

    from_freqs = 400
    to_freqs = 600

    # threads = []
    # for sensorn in range(len(Sensors)):
    #     t = threading.Thread(target=worker, args=(sensorn, files, to_freqs, from_freqs, FS, baseblocksize, datapath,
    #                                               cwd, downsample_factor))
    #     threads.append(t)
    #     t.start()
    worker(2, files, to_freqs, from_freqs, FS, baseblocksize, datapath, cwd, downsample_factor)
    os.chdir(cwd)


def getInfoOfRawDataFolder(PATH_TO_DATA):
    result = dict()
    filenames = glob.glob(PATH_TO_DATA + '/*.tdms')

    pbar = tqdm(total=len(filenames))

    for filename in filenames:
        tdmsf = TdmsFile(os.path.join(PATH_TO_DATA, filename))
        pbar.set_description(f'Processing {filename}')
        for group in tdmsf.groups():
            for channel in tdmsf.group_channels(group):
                if len(channel.data) < 5:
                    continue
                if ('unit_string' in channel.properties) and channel.property('unit_string') == 'RAW':
                    if channel.path in result:
                        if len(channel.data) in result[channel.path]:
                            result[channel.path][len(channel.data)] += 1
                        else:
                            result[channel.path][len(channel.data)] = 1
                    else:
                        result[channel.path] = {len(channel.data): 1}
        pbar.update(1)

    print(result)
    return result


def plotTimesOfData(PATH_TO_DATA):
    filenames = glob.glob(PATH_TO_DATA + '/*.tdms')
    x = []
    y = []

    for filename in filenames:
        time = filename[len(filename) - 18:len(filename) - 5]
        x.append(datetime.strptime(time, '%y%m%d_%H%M%S'))
        y.append(1)
    plt.scatter(x, y)
    plt.show()


def getFilenamesFromTimeToTime(datapath, timeFrom, timeTo):
    filenames = glob.glob(datapath + '/*.tdms')
    yearRange = range(int(timeFrom[2:4]), int(int(timeTo[2:4]) + 1))
    monthRange = range(int(timeFrom[5:7]), int(int(timeTo[5:7]) + 1))
    dayRange = range(int(timeFrom[8:10]), int(int(timeTo[8:10]) + 1))
    result = []
    for filename in filenames:
        timestring = filename[len(filename) - 18:len(filename) - 5]
        if (int(timestring[:2]) in yearRange) and (int(timestring[2:4]) in monthRange) \
                and (int(timestring[4:6]) in dayRange):
            result.append(filename)
    return sorted(result)


def insertTimestampsToDB(path):
    companyName = path.split('/')[-1]
    connGet = MySQLdb.connect(host="172.16.23.204", user="fourdot", passwd="4d0tFourdot", db="dp")
    cursor = connGet.cursor()
    sql_query = "SELECT id FROM plot WHERE company = \'{}\'".format(companyName)
    cursor.execute(sql_query)
    plotID = cursor.fetchall()[0][0]
    print(plotID)
    filenames = glob.glob(path + '/*.tdms')
    for filename in filenames:
        timestring = filename[len(filename) - 18:len(filename) - 5]
        print(timestring)
        print(time.mktime(datetime.strptime(timestring, "%y%m%d_%H%M%S").timetuple()))
        exit(1)
        print()
    return True


if __name__ == '__main__':
    insertTimestampsToDB(PATHS_TO_COMPANIES[0])

    # conn_get = MySQLdb.connect(host="172.16.23.204", user="fourdot", passwd="4d0tFourdot", db="chipmunk")
    # sql_query = "SELECT time,value FROM analysis_value " \
    #             "WHERE (senzor = 1) ORDER BY time"
    # cursor.execute(sql_query)
    # rows = cursor.fetchall()
    # data = []
    # timestamps = []
    #
    # for row in rows:
    #     timestamps.append(row[0])
    #     data.append(row[1])
    # x = plt.plot(timestamps, data)
    # plt.show()
