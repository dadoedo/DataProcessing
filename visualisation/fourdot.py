import MySQLdb

from datetime import datetime
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

conn = MySQLdb.connect(host="xxx", user="xxx", passwd="xxx", db="xxx")
cursor = conn.cursor()
sql_query = "SELECT time,value FROM analysis_state " \
            "INNER JOIN analysis_value ON analysis_state.id = analysis_value.analysis_state_id " \
            "WHERE (analysis_id = 763) ORDER BY time"
cursor.execute(sql_query)
rows = cursor.fetchall()
data = []
timestamps = []
for row in rows:
    timestamps.append(datetime.utcfromtimestamp(row[0]).strftime('%Y-%m-%d %H:%M:%S'))
    data.append(row[1])

sql_query = "SELECT time,value FROM analysis_state " \
            "INNER JOIN analysis_value ON analysis_state.id = analysis_value.analysis_state_id " \
            "WHERE (analysis_id = 764) ORDER BY time"
cursor.execute(sql_query)
rows = cursor.fetchall()
data_2 = []
timestamps_2 = []
for row in rows:
    timestamps_2.append(datetime.utcfromtimestamp(row[0]).strftime('%Y-%m-%d %H:%M:%S'))
    data_2.append(row[1])

# conn = MySQLdb.connect(host="xxx", user="xxx", passwd="xxx", db="xxx")
# cursor = conn.cursor()
# sql_query = "SELECT time,value FROM analysis_value WHERE senzor = 2 " \
#             "ORDER BY time"
# cursor.execute(sql_query)
# rows = cursor.fetchall()
# data_chipmunk = []
# timestamps_chipmunk = []
# last_time_entry = None
# for row in rows:
#     timestamps_chipmunk.append(datetime.utcfromtimestamp(float(row[0])/1000).strftime('%Y-%m-%d %H:%M:%S.%f'))
#     data_chipmunk.append(row[1])

layout = html.Div(children=[
    html.H2(
        children='4dot device example',
        style={
            'textAlign': 'center',
        }
    ),
    dcc.Link('Home', href='/', style={'textAlign': 'right'}),
    html.Div(id='output-mat-graphs'),
    dcc.Graph(
        figure={
            'data': [
                go.Scatter(
                    x=timestamps,
                    y=data,
                )
            ],
            'layout': {
                'title': 'Example Device, front bearing'
            }
        }
    ),
    dcc.Graph(
        figure={
            'data': [
                go.Scatter(
                    x=timestamps_2,
                    y=data_2,
                )
            ],
            'layout': {
                'title': 'Example Device, back bearing'
            }
        }
    ),
    # dcc.Graph(
    #     figure={
    #         'data': [
    #             go.Scatter(
    #                 x=timestamps_chipmunk,
    #                 y=data_chipmunk,
    #             )
    #         ],
    #         'layout': {
    #             'title': 'Example Chipmunk'
    #         }
    #     }
    # ),
])

if __name__ == '__main__':
    conn = MySQLdb.connect(host="172.16.23.204", user="fourdot", passwd="4d0tFourdot", db="dat_16")
    cursor = conn.cursor()
    sql_query = "SELECT time,value FROM analysis_state " \
                "INNER JOIN analysis_value ON analysis_state.id = analysis_value.analysis_state_id " \
                "WHERE (analysis_id = 763) ORDER BY time"
    cursor.execute(sql_query)
    rows = cursor.fetchall()
    data = []
    timestamps = []
    for row in rows:
        timestamps.append(row[0])
        data.append(row[1])

    print(data)
