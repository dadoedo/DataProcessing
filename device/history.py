import glob
import ntpath

import MySQLdb
from datetime import datetime
from nptdms import TdmsFile
import json
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

from dash.dependencies import Input, Output
from app import app

conn_get = MySQLdb.connect(host="172.16.23.204", user="fourdot", passwd="4d0tFourdot", db="dp")
cursor = conn_get.cursor()

layout = None


@app.callback(Output('output-history-graph', 'children'), [
    Input('sensor-dropdown', 'value')
])
def historyGraphOutput(plotId):
    if plotId is None:
        return

    query = "select timestamp, value, type from data_entry where plot_id = \"{}\" " \
            "order by timestamp asc, type".format(plotId)
    cursor.execute(query)
    rows = cursor.fetchall()

    if len(rows) < 2:
        return None

    graphs = []
    xAxis = []
    yAxis = []

    actualType = -1

    for row in rows:
        if actualType != row[2]:
            if actualType != -1:
                graphs.append(dcc.Graph(
                    figure={
                        'data': [
                            go.Scatter(
                                x=xAxis,
                                y=yAxis,
                            )],
                        'layout': {
                            'title': "Type {}".format(row[2]),
                            'yaxis': {
                                'title': 'Amplitude'
                            }
                        }
                    }
                ))
            yAxis = []
            xAxis = []

        xAxis.append(datetime.utcfromtimestamp(row[0]).strftime('%Y-%m-%d %H:%M:%S'))
        yAxis.append(row[1])
        actualType = row[2]

    graphs.append(dcc.Graph(
        figure={
            'data': [
                go.Scatter(
                    x=xAxis,
                    y=yAxis,
                )],
            'layout': {
                'title': "Type {}".format(rows[len(rows) - 1][2]),
                'yaxis': {
                    'title': 'Amplitude'
                }
            }
        }
    ))

    return graphs


def getSensorDropdowns(deviceId):
    query = "select sensor, id from plot where device_id = \"{}\"".format(deviceId)
    cursor.execute(query)
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({'label': "Sensor {}".format(row[0]), 'value': row[1]})

    return result


def returnLayout(deviceId):
    query = "select name from device where id = \"{}\"".format(deviceId)
    cursor.execute(query)
    deviceName = cursor.fetchone()[0]
    global layout
    layout = html.Div(children=[
        html.H2(
            children=deviceName,
            style={
                'textAlign': 'center',
            },
            id="header-h2"
        ),
        dcc.Link('Home', href='/', style={'textAlign': 'right'}),
        dcc.Dropdown(id='sensor-dropdown', options=getSensorDropdowns(deviceId),
                     searchable=False),
        html.Div(id='output-history-graph'),
    ])

    return layout
