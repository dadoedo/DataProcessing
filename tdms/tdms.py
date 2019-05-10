import glob
import ntpath

from nptdms import TdmsFile
import json
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from app import app

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
from app import app

conn_get = MySQLdb.connect(host="172.16.23.204", user="fourdot", passwd="4d0tFourdot", db="dp")
cursor = conn_get.cursor()


def generate_dropdown_inputs(directory_path, file_type):
    if directory_path[-1:] is not '/':
        directory_path = directory_path + '/'
    tdms_filenames = glob.glob(directory_path + '**/*.{}'.format(file_type), recursive=True)
    result = []
    for name in tdms_filenames:
        result.append({'label': ntpath.basename(name), 'value': name})
    return result


layout = html.Div(children=[
    html.H2(
        children='4dot raw Data',
        style={
            'textAlign': 'center',
        }
    ),
    dcc.Link('Home', href='/', style={'textAlign': 'right'}),
    dcc.Dropdown(id='filename_dropdown',
                 options=
                 # tdms_files.generate_dropdown_inputs('/home/david/Documents/4dot_data/example_data', 'tdms'),
                 generate_dropdown_inputs("/home/david/HDD/PSL", 'tdms'),
                 ),
    html.Div(id='output-tdms-graphs'),
])


@app.callback(Output('output-tdms-graphs', 'children'),
              [
                  Input('filename_dropdown', 'value')
              ],
              )
def update_output(path):
    if path is not None:
        tdms_file = TdmsFile(path)
        root = tdms_file.object()

        filename = ntpath.basename(path).split('.')[0]
        children = [html.H3('{}'.format(filename), style={'textAlign': 'center'}),
                    ]
        date = "20{}-{}-{} {}:{}:{}".format(filename.split('_')[-2][:2], filename.split('_')[-2][2:4],
                                            filename.split('_')[-2][4:6], filename.split('_')[-1][:2],
                                            filename.split('_')[-1][2:4], filename.split('_')[-1][4:6])
        children.append(html.H4("Captured @ {}".format(date), style={'textAlign': 'center'}))

        for g in tdms_file.groups():
            children.append(html.H5('Group of Channels: Name = {}'.format(g), style={'textAlign': 'center'}))

            for c in tdms_file.group_channels(g):
                if len(c.data) > 3:
                    if 'Description' in c.properties:
                        children.append(mat.plot_graph(c.data, 'Channel Name = {}, SF = {}, time = {}s'.format(
                            c.channel, json.loads(c.property('Description'))['sf'],
                            len(c.data) / json.loads(c.property('Description'))['sf'])))
                    else:
                        children.append(mat.plot_graph(c.data, 'Channel Name = {}'.format(c.channel)))
                else:
                    children.append(html.H5('Channel Name = {}, {} samples'.format(c.channel, len(c.data)),
                                            style={'textAlign': 'center'}))
                    children.append(html.H5('Data = {}'.format(c.data), style={'textAlign': 'center'}))
        return children


if __name__ == '__main__':
    dfPlots = []
    thresholds = [1497452868, 1503470949, 1536753628, 1442147708, 1443207510, 1536749823]
    for i in [10, 158, 161, 661, 662, 880]:
        dfPlots.append(pd.DataFrame.from_csv('/home/david/Documents/4dot_data/processed_plots/{}.csv'.format(i)))

    dfPlotsWDate = []
    for dfPlot in dfPlots:
        dfPlotsWDate.append(
            pd.DataFrame({'timestamp': pd.to_datetime(dfPlot['timestamp'], unit='ms'), 'y': dfPlot['y']}))

    print(len(dfPlotsWDate))
    for i, p in enumerate(dfPlotsWDate):
        plt.figure()
        ax = plt.gca()
        p.plot(kind='line', x='timestamp', y='y', color='blue', ax=ax)
        plt.axvline(x=datetime.datetime.fromtimestamp(thresholds[i]), color='red')
        plt.show()

