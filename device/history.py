import glob
import ntpath

import MySQLdb
import datetime
import random
import json
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from nptdms import TdmsFile
from plotly.tools import mpl_to_plotly
from fbprophet import Prophet
from scipy.special import inv_boxcox
from scipy.stats import boxcox
from dash.dependencies import Input, Output, State

from app import app

conn_get = MySQLdb.connect(host="172.16.23.204", user="fourdot", passwd="4d0tFourdot", db="dp")
cursor = conn_get.cursor()

layout = None

MEAN_AVERAGE_TYPE = 1
RMS_TYPE = 2
VARIANCE_TYPE = 3
SKEWNESS_TYPE = 4
COMPANY_TYPE = 10
typeToHeadings = {
    MEAN_AVERAGE_TYPE : 'Simple mean average of each file',
    RMS_TYPE : 'RMS of each file [FS / 100]',
    VARIANCE_TYPE : 'Variance',
    SKEWNESS_TYPE : 'Skewness',
    COMPANY_TYPE : 'Processed data [by partnered company]',
}


@app.callback(Output('output-prophet-graph', 'children'),
            [Input('prophet-button', 'n_clicks'),],
            [State('sensor-dropdown', 'value') ,
             State('radio-items-type-prophet', 'value')])
def computeProphetPrediction(n_clicks, plot_setId, plotType):
    if n_clicks is None or plotType is None:
        return None
    if plotType is None:
        return html.Label("Select plot, for which to compute")

    print("------------------- PROPHET START -------------------")
    query = "select timestamp, value, type from data_entry where plot_set_id = \"{}\" and type = \"{}\"" \
            "order by type, timestamp asc".format(plot_setId, plotType)

    vibrations = pd.read_sql(query, conn_get)
    if len(vibrations) < 2:
        return html.Label('Unavailable plot')

    vibrations = vibrations.rename(index=str, columns={"timestamp": "date"})
    vibrations['date'] = pd.to_datetime(vibrations['date'], unit='s')
    vibrations.set_index('date')
    vibrations = vibrations[['date', 'value']]

    data = pd.read_sql(query, conn_get)

    lastDate = vibrations['date'][-1]
    firstDate = vibrations['date'][0]

    daysToForecast =  ((lastDate - firstDate) / 3).days

    lastDate = str(lastDate)
    firstDate = str(firstDate)

    cursor.execute("SELECT sensor FROM plot_set WHERE id = {}".format(plot_setId))
    sensorName = cursor.fetchone()[0]

    df = vibrations.reset_index()
    df = df.rename(columns={'date': 'ds', 'value': 'y'})

    belowZeroValue = None
    if df['y'].min() < 0:
        belowZeroValue = abs(df['y'].min()) + 0.1
        df['y'] = df['y'] + belowZeroValue

    df['y'], lam = boxcox(df['y']) # transformsa data, stores lambda key for retransform

    m = Prophet(seasonality_mode='multiplicative').fit(df)
    future = m.make_future_dataframe(periods=daysToForecast)
    fcst = m.predict(future)

    vibrations = vibrations.rename(index=str, columns={"date": "ds"})
    vibrations.set_index('ds', inplace=True)
    df.set_index('ds', inplace=True)
    fcst.set_index('ds', inplace=True)
    viz_df = vibrations.join(fcst[['yhat', 'yhat_lower', 'yhat_upper']], how='outer')
    viz_df[['yhat', 'yhat_upper', 'yhat_lower']] = viz_df[['yhat', 'yhat_upper', 'yhat_lower']].apply(
        lambda x: inv_boxcox(x, lam))
    if belowZeroValue is not None:
        viz_df[['yhat', 'yhat_upper', 'yhat_lower']] = viz_df[['yhat', 'yhat_upper', 'yhat_lower']] - abs(belowZeroValue)

    removeExteremeUncertainitiesMask = viz_df.yhat_upper > viz_df.value.max() * 3
    viz_df.loc[removeExteremeUncertainitiesMask, 'yhat_upper'] = None
    removeExteremeUncertainitiesMask = viz_df.yhat_lower > viz_df.value.min() * 3
    viz_df.loc[removeExteremeUncertainitiesMask, 'yhat_lower'] = None

    print("------------------- PROPHET END -------------------")
    return [ dcc.Graph(id="graph-type-{}".format(type),
               figure={
                   'data': [
                       go.Scatter(
                           y=viz_df.yhat_upper,
                           x=viz_df.index,
                           line=dict(color='rgba(255,255,255,0)'),
                           showlegend=False,
                           name='Forecasted Vibrations',
                       ),
                       go.Scatter(
                           y=viz_df.yhat_lower,
                           x=viz_df.index,
                           fill='tonexty',
                           fillcolor='rgba(0,100,80,0.2)',
                           line=dict(color='rgba(255,255,255,0)'),
                           showlegend=False,
                           name='Forecasted Vibrations',
                       ),
                       go.Scatter(
                           y=viz_df.value,
                           x=viz_df.index,
                           name= 'Actual Vibrations'
                       ),
                        go.Scatter(
                           y=viz_df.yhat,
                           x=viz_df.index,
                           line = {'dash' : 'dot', 'color' : 'rgb(0,0,0,175)'},
                           name= 'Forecasted Vibrations'
                        ),],
                   'layout': {
                       'title': 'Vibrations vs Vibrations Forecast (Dots)',
                       'yaxis': {
                           'title': 'Amplitude'
                       }
                   }
             })
             ]


@app.callback(Output('output-history-graph', 'children'), [
    Input('sensor-dropdown', 'value')
])
def historyGraphOutput(plot_setId):
    if plot_setId is None:
        return
    query = "select timestamp, value, type from data_entry where plot_set_id = \"{}\" " \
            "order by type, timestamp asc".format(plot_setId)
    data = pd.read_sql(query, conn_get)
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='s')
    grouped = data.groupby('type')
    length = len(data)

    if False:
        for i, (index, row) in enumerate(data.iterrows()):
            if i == length - 2:
                break

            if row['type'] != data.loc[index + 1]['type']:
                continue

            if data.loc[index + 1]['timestamp'] - row['timestamp'] > datetime.timedelta(hours=8):
                data = pd.concat([data.loc[0:index],
                           pd.DataFrame({'timestamp': [row['timestamp'] + datetime.timedelta(seconds=1),
                                                       row['timestamp'] + datetime.timedelta(seconds=2),
                                                       data.loc[index + 1]['timestamp'] - datetime.timedelta(seconds=2),
                                                       data.loc[index + 1]['timestamp'] - datetime.timedelta(seconds=1)],
                                         'value': [0, 0, 0, 0],  # [],
                                         'type': [row['type'],row['type'],row['type'],row['type']]},  # 4x type
                                        index=[0,0,0,0]),
                           data.loc[index + 1:]], ignore_index=True)

    graphs = []

    for type in data['type'].unique():
        graphs.append(dcc.Graph(id="graph-type-{}".format(type),
            figure={
                'data': [
                    go.Scatter(
                        x=grouped["timestamp"].get_group(type),
                        y=grouped["value"].get_group(type),
                    )],
                'layout': {
                    'title': typeToHeadings[type],
                    'yaxis': {
                        'title': 'Amplitude'
                    }
                }
            }
        ))

    graphs.append(html.Label("Compute Prophet predictions for :"))
    options = []
    for key, value in typeToHeadings.items():
        options.append({'label': value, 'value': key})

    graphs.append(dcc.RadioItems(
        id='radio-items-type-prophet',
        options=options,
    ))
    graphs.append(html.Button("Compute Prophet prediction", id='prophet-button'))
    for i in range(0,5):
        graphs.append(html.Br())

    return graphs


def getSensorDropdowns(deviceId):
    query = "select sensor, id from plot_set where device_id = \"{}\"".format(deviceId)
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
    if not deviceName:
        return html.Div("Bad Link!")

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
        html.Label('Select Sensor on Deivce'),
        dcc.Dropdown(id='sensor-dropdown', options=getSensorDropdowns(deviceId),
                     searchable=False),
        html.Div(id='output-history-graph'),
        html.Br(),
        html.Div(id='output-prophet-graph'),
    ])

    return layout


if __name__ == '__main__':
    plot_setId = 21
    daysToForecast = 30

    query = "select timestamp, value, type from data_entry where plot_set_id = \"{}\" and type = \'2\'" \
            "order by type, timestamp asc".format(plot_setId)

    vibrations = pd.read_sql(query, conn_get)
    vibrations = vibrations.rename(index=str, columns={"timestamp": "date"})
    vibrations['date'] = pd.to_datetime(vibrations['date'], unit='s')
    vibrations.set_index('date')
    vibrations = vibrations[['date', 'value']]

    lastDate = str(vibrations['date'][-1])
    firstDate = str(vibrations['date'][0])
    cursor.execute("SELECT sensor FROM plot_set WHERE id = {}".format(plot_setId))
    sensorName = cursor.fetchone()[0]

    df = vibrations.reset_index()
    df = df.rename(columns={'date': 'ds', 'value': 'y'})

    df.set_index('ds').y.plot_set()
    plt.title('Original Data\nSensor : {} [plot_set ID - {}]\n{} - {}\nDTF = {}'.format(
        sensorName, plot_setId, firstDate, lastDate, daysToForecast
    ))
    # plt.savefig("/home/david/Desktop/prophet_od_{}_{}.svg".format(plot_setId, daysToForecast))
    plt.show()
    plt.clf()

    # transformation

    # df['y'] = np.log(df['y'])
    df['y'], lam = boxcox(df['y']) # transformsa data, stores lambda key for retransform
    df.set_index('ds').y.plot_set()

    plt.title('Transformed Data\nSensor : {} [plot_set ID - {}]\n{} - {}\nDTF = {}'.format(
        sensorName, plot_setId, firstDate, lastDate, daysToForecast
    ))
    # plt.savefig("/home/david/Desktop/prophet_td_{}_{}.svg".format(plot_setId,daysToForecast))
    plt.show()
    plt.clf()

    # Prophecy
    m = Prophet(seasonality_mode='multiplicative').fit(df)
    future = m.make_future_dataframe(periods=daysToForecast)
    fcst = m.predict(future)

    m.plot(fcst)
    plt.title('Prophet Forecast Data\nSensor : {} [plot_set ID - {}]\n{} - {}\nDTF = {}'.format(
        sensorName,plot_setId,firstDate,lastDate,daysToForecast
    ))
    # plt.savefig("/home/david/Desktop/prophet_pd_{}_{}.svg".format(plot_setId,daysToForecast))
    plt.show()
    plt.clf()

    vibrations = vibrations.rename(index=str, columns={"date": "ds"})
    vibrations.set_index('ds', inplace=True)
    df.set_index('ds', inplace=True)
    fcst.set_index('ds', inplace=True)
    viz_df = vibrations.join(fcst[['yhat', 'yhat_lower', 'yhat_upper']], how='outer')
    viz_df[['yhat', 'yhat_upper', 'yhat_lower']] = viz_df[['yhat', 'yhat_upper', 'yhat_lower']].apply(
        lambda x: inv_boxcox(x, lam))

    plt.plot(viz_df.value, linewidth=0.7)
    plt.plot(viz_df.yhat, color='orange', linewidth=0.8)
    plt.fill_between(viz_df.index, viz_df['yhat_upper'], viz_df['yhat_lower'], alpha=0.2, color='darkorange')
    plt.title('Prophet Transformed Back Data\nSensor : {} [plot_set ID - {}]\n{} - {}\nDTF = {}'.format(
        sensorName, plot_setId, firstDate, lastDate, daysToForecast
    ))
    plt.savefig("/home/david/Desktop/prophet_ptbd_{}_{}.svg".format(plot_setId, daysToForecast))
    plt.show()
    plt.clf()

    ### final graph
    connect_date = vibrations.index[-2]
    mask = (fcst.index > connect_date)
    predict_df = fcst.loc[mask]
    viz_df = vibrations.join(predict_df[['yhat', 'yhat_lower', 'yhat_upper']], how='outer')
    viz_df[['yhat', 'yhat_upper', 'yhat_lower']] = viz_df[['yhat', 'yhat_upper', 'yhat_lower']].apply(
        lambda x: inv_boxcox(x, lam))

    fig, ax1 = plt.subplots()
    ax1.plot(viz_df.value, )
    ax1.plot(viz_df.yhat, color='black', linestyle=':')
    ax1.fill_between(viz_df.index, viz_df['yhat_upper'], viz_df['yhat_lower'], alpha=0.5,
                     color='darkgray')
    ax1.set_title('Vibrations (Blue) vs Vibrations Forecast (Black)')
    ax1.set_ylabel('Vibrations Amplitude')
    ax1.set_xlabel('Date')

    L = ax1.legend()  # get the legend
    L.get_texts()[0].set_text('Actual Vibrations')  # change the legend text for 1st plot
    L.get_texts()[1].set_text('Forecasted Vibrations')  # change the legend text for 2nd plot
    plt.savefig("/home/david/Desktop/prophet_pfinal_{}_{}.svg".format(plot_setId, daysToForecast))
    plt.show()

    print("DONE.")
