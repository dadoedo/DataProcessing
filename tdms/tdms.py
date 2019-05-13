import glob
import ntpath

from nptdms import TdmsFile
import json
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
# from app import app

import glob
import ntpath

import MySQLdb
import datetime
import random
from nptdms import TdmsFile
import json
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from plotly.tools import mpl_to_plotly
import pandas as pd
import numpy as np
from fbprophet import Prophet
import matplotlib.pyplot as plt
from scipy.special import inv_boxcox
from scipy.stats import boxcox
import csv

from dash.dependencies import Input, Output, State
# from app import app

conn_get = MySQLdb.connect(host="172.16.23.204", user="fourdot", passwd="4d0tFourdot", db="dp")
cursor = conn_get.cursor()

#
# def generate_dropdown_inputs(directory_path, file_type):
#     if directory_path[-1:] is not '/':
#         directory_path = directory_path + '/'
#     tdms_filenames = glob.glob(directory_path + '**/*.{}'.format(file_type), recursive=True)
#     result = []
#     for name in tdms_filenames:
#         result.append({'label': ntpath.basename(name), 'value': name})
#     return result
#
#
# layout = html.Div(children=[
#     html.H2(
#         children='4dot raw Data',
#         style={
#             'textAlign': 'center',
#         }
#     ),
#     dcc.Link('Home', href='/', style={'textAlign': 'right'}),
#     dcc.Dropdown(id='filename_dropdown',
#                  options=
#                  # tdms_files.generate_dropdown_inputs('/home/david/Documents/4dot_data/example_data', 'tdms'),
#                  generate_dropdown_inputs("/home/david/HDD/PSL", 'tdms'),
#                  ),
#     html.Div(id='output-tdms-graphs'),
# ])
#
#
# @app.callback(Output('output-tdms-graphs', 'children'),
#               [
#                   Input('filename_dropdown', 'value')
#               ],
#               )
# def update_output(path):
#     if path is not None:
#         tdms_file = TdmsFile(path)
#         root = tdms_file.object()
#
#         filename = ntpath.basename(path).split('.')[0]
#         children = [html.H3('{}'.format(filename), style={'textAlign': 'center'}),
#                     ]
#         date = "20{}-{}-{} {}:{}:{}".format(filename.split('_')[-2][:2], filename.split('_')[-2][2:4],
#                                             filename.split('_')[-2][4:6], filename.split('_')[-1][:2],
#                                             filename.split('_')[-1][2:4], filename.split('_')[-1][4:6])
#         children.append(html.H4("Captured @ {}".format(date), style={'textAlign': 'center'}))
#
#         for g in tdms_file.groups():
#             children.append(html.H5('Group of Channels: Name = {}'.format(g), style={'textAlign': 'center'}))
#
#             for c in tdms_file.group_channels(g):
#                 if len(c.data) > 3:
#                     if 'Description' in c.properties:
#                         children.append(mat.plot_graph(c.data, 'Channel Name = {}, SF = {}, time = {}s'.format(
#                             c.channel, json.loads(c.property('Description'))['sf'],
#                             len(c.data) / json.loads(c.property('Description'))['sf'])))
#                     else:
#                         children.append(mat.plot_graph(c.data, 'Channel Name = {}'.format(c.channel)))
#                 else:
#                     children.append(html.H5('Channel Name = {}, {} samples'.format(c.channel, len(c.data)),
#                                             style={'textAlign': 'center'}))
#                     children.append(html.H5('Data = {}'.format(c.data), style={'textAlign': 'center'}))
#         return children
#

if __name__ == '__main__':
    dfPlots = []
    thresholds = [1497452868, 1503470949, 1536753628, 1442147708, 1443207510, 1536749823]
    # for i in [10, 158, 161, 661, 662, 880]:
    #     df_csv = pd.DataFrame.from_csv('/home/david/Documents/4dot_data/processed_plots/{}.csv'.format(i))
    #     df_csv.drop_duplicates('timestamp')
    #     dfPlots.append(df_csv)
    #
    # dfPlotsWDate = []
    # for dfPlot in dfPlots:
    #     dfPlotsWDate.append(
    #         pd.DataFrame({'timestamp': pd.to_datetime(dfPlot['timestamp'], unit='ms'), 'y': dfPlot['y']}))
    # #
    # for df in dfPlotsWDate:
    #     df.drop_duplicates({'timestamp'})

    # print(len(dfPlotsWDate))
    # for i, p in enumerate(dfPlotsWDate):
    #     plt.figure()
    #     ax = plt.gca()
    #     p.plot(kind='line', x='timestamp', y='y', color='blue', ax=ax)
    #     plt.axvline(x=datetime.datetime.fromtimestamp(thresholds[i]), color='red')
    #     plt.show()

    dfPlotIDs = [11, 6, 7, 20, 21, 8]
    for index, i in enumerate([10, 158, 161, 661, 662, 880]):
        print("PLOT {} - file {}".format(dfPlotIDs[index], i))
        df_csv = pd.DataFrame.from_csv('/home/david/Documents/4dot_data/processed_plots/{}.csv'.format(i))
        df = df_csv.drop_duplicates('timestamp')
        df = pd.DataFrame({'timestamp': pd.to_datetime(df['timestamp'], unit='ms'), 'y': df['y']})

        query = "INSERT INTO data_entry VALUES " + "\n"
        valuesQuery = ""
        deviceId = -1
        if i in [158, 161, 880]:
            deviceId = [1, 2]
        if i is 10:
            deviceId = 3
        if i in [661, 662]:
            deviceId = 4

        timeFrom = None
        timeTo = None

        if not isinstance(deviceId, list):
            if deviceId is 3:
                timeFrom = datetime.datetime(year=2016, month=11, day=23)
                timeTo = datetime.datetime(year=2016, month=11, day=23)
            if deviceId is 4:
                timeFrom = datetime.datetime(year=2015, month=9, day=10)
                timeTo = datetime.datetime(year=2015, month=10, day=9)

            mask = ((df['timestamp'] >= timeFrom) & (df['timestamp'] <= timeTo))
            df = df[mask]

            print("len of df - {}".format(len(df)))
            if len(df) is 0:
                continue

            print("inserting")
            df.head()
            for z, row in df.iterrows():
                valuesQuery = valuesQuery + "({}, {}, {}, {}),\n".format(int(datetime.datetime.timestamp(row['timestamp'])), row['y'], 10, dfPlotIDs[index])

            if valuesQuery is "":
                continue

            query = query + valuesQuery
            query = query[:-2]

            cursor.execute(query)
            conn_get.commit()
            continue

        maskForA = ((df['timestamp'] >= datetime.datetime(year=2017, month=5, day=30)) &
                    (df['timestamp'] <= datetime.datetime(year=2017, month=8, day=20)))

        maskForB = ((df['timestamp'] >= datetime.datetime(year=2018, month=5, day=21)) &
                    (df['timestamp'] <= datetime.datetime(year=2018, month=12, day=1)))

        dfA = df[maskForA]
        print(dfA.head())
        if len(dfA) is not 0:
            for z, row in dfA.iterrows():
                print(datetime.datetime.timestamp(row['timestamp']), row['y'])
                valuesQuery = valuesQuery + "({}, {}, {}, {}),\n".format(int(datetime.datetime.timestamp(row['timestamp'])), row['y'], 10, dfPlotIDs[index])

        if valuesQuery is not "":
            query = query + valuesQuery
            query = query[:-2]
            print("HERE __ COMMIT")

            cursor.execute(query)
            conn_get.commit()

        query = "INSERT INTO data_entry VALUES " + "\n"
        valuesQuery = ""
        dfB = df[maskForB]
        print(dfB.head(15))
        if len(dfB) is not 0:
            for z, row in dfB.iterrows():
                valuesQuery = valuesQuery + "({}, {}, {}, {}),\n".format(int(datetime.datetime.timestamp(row['timestamp'])), row['y'], 10, dfPlotIDs[index] + 18)

        if valuesQuery is not "":
            query = query + valuesQuery
            query = query[:-2]

            cursor.execute(query)
            conn_get.commit()


