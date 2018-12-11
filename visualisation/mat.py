import glob
import inspect
import ntpath
from array import array
import numpy as np

import scipy.io as sio
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, Event

from app import app
import plotly.graph_objs as go
from tdms_processing import tdms_files


def plot_graph(data, name):
    return dcc.Graph(
        figure={
            'data': [
                go.Scatter(
                    y=data,
                )
            ],
            'layout': {
                'title': '{}'.format(name)
            }
        }
    )


def plot(value):
    div_children = []
    mat_file = sio.loadmat(value, squeeze_me=True)
    for k in mat_file:
        if k[:2] != "__" and k[-3:] != "RPM":
            div_children.append(plot_graph(mat_file[k], k))
    div = html.Div(children=div_children)
    return div


def plots_from_mat_file(filename):
    div_children = []
    mat_file = sio.loadmat(filename, squeeze_me=True)
    for k in mat_file:
        if k[:2] != "__" and k[-3:] != "RPM":
            div_children.append(plot_graph(k, mat_file[k]))
    div = html.Div(children=div_children)
    return div


layout = html.Div(children=[
    html.H2(
        children='Bearing Data Center example data',
        style={
            'textAlign': 'center',
        }
    ),
    dcc.Link('Home', href='/', style={'textAlign': 'right'}),
    html.Table(style={'textAlign': 'center'},
               children=[
                   html.Tr(children=[
                       html.Th('Fault Diameter'),
                       html.Th('Motor Load (HP)'),
                       html.Th('Approx. Motor Speed (rpm)'),
                       html.Th('Inner Race'),
                       html.Th('Ball'),
                       html.Th('Outer Race\nPosition Relative to Load Zone (Load Zone Centered at 6:00)', colSpan=3),
                   ]
                   ),
                   html.Tr(children=[
                       html.Th(''),
                       html.Th(''),
                       html.Th(''),
                       html.Th(''),
                       html.Th(''),
                       html.Th('Centered'),
                       html.Th('Orthogonal'),
                       html.Th('Opposite'),
                   ]
                   ),
                   html.Tr(children=[
                       html.Td('0.007'),
                       html.Td('0'),
                       html.Td('1797'),
                       html.Td(html.Button('IR007_0', id='IR007_0', value='/home/david/Documents/BDC_data/105.mat'),
                               n_clicks_timestamp=-1),
                       html.Td(html.Button('B007_0', id='B007_0', value='/home/david/Documents/BDC_data/118.mat'),
                               n_clicks_timestamp=-1),
                       html.Td(
                           html.Button('OR007at6_0', id='OR007at6_0', value='/home/david/Documents/BDC_data/130.mat'),
                           n_clicks_timestamp=-1),
                       html.Td(
                           html.Button('OR007at3_0', id='OR007at3_0', value='/home/david/Documents/BDC_data/144.mat'),
                           n_clicks_timestamp='-1'),
                       html.Td(
                           html.Button('OR007at12_0', id='OR007at12_0', value='/home/david/Documents/BDC_data/156.mat'),
                           n_clicks_timestamp='-1'),
                   ]
                   ),
                   html.Tr(children=[
                       html.Td(''),
                       html.Td('1'),
                       html.Td('1772'),
                       html.Td(html.Button('IR007_1', id='IR007_1', value='/home/david/Documents/BDC_data/106.mat'),
                               n_clicks_timestamp='-1'),
                       html.Td(html.Button('B007_1', id='B007_1', value='/home/david/Documents/BDC_data/119.mat'),
                               n_clicks_timestamp='-1'),
                       html.Td(
                           html.Button('OR007at6_1', id='OR007at6_1', value='/home/david/Documents/BDC_data/131.mat'),
                           n_clicks_timestamp='-1'),
                       html.Td(
                           html.Button('OR007at3_1', id='OR007at3_1', value='/home/david/Documents/BDC_data/145.mat'),
                           n_clicks_timestamp='-1'),
                       html.Td(
                           html.Button('OR007at12_1', id='OR007at12_1', value='/home/david/Documents/BDC_data/158.mat'),
                           n_clicks_timestamp='-1'),
                   ]
                   ),
                   html.Tr(children=[
                       html.Td(''),
                       html.Td('2'),
                       html.Td('1750'),
                       html.Td(html.Button('IR007_2', id='IR007_2', value='/home/david/Documents/BDC_data/106.mat'),
                               n_clicks_timestamp='-1'),
                       html.Td(html.Button('B007_2', id='B007_2', value='/home/david/Documents/BDC_data/119.mat'),
                               n_clicks_timestamp='-1'),
                       html.Td(
                           html.Button('OR007at6_2', id='OR007at6_2', value='/home/david/Documents/BDC_data/131.mat'),
                           n_clicks_timestamp='-1'),
                       html.Td(
                           html.Button('OR007at3_2', id='OR007at3_2', value='/home/david/Documents/BDC_data/145.mat'),
                           n_clicks_timestamp='-1'),
                       html.Td(
                           html.Button('OR007at12_2', id='OR007at12_2', value='/home/david/Documents/BDC_data/158.mat'),
                           n_clicks_timestamp='-1'),
                   ]
                   ),
                   html.Tr(children=[
                       html.Td(''),
                       html.Td('3'),
                       html.Td('1730'),
                       html.Td(html.Button('IR007_3', id='IR007_3', value='/home/david/Documents/BDC_data/108.mat',
                                           n_clicks_timestamp='-1')),
                       html.Td(html.Button('B007_3', id='B007_3', value='/home/david/Documents/BDC_data/121.mat',
                                           n_clicks_timestamp='-1')),
                       html.Td(
                           html.Button('OR007at6_3', id='OR007at6_3', value='/home/david/Documents/BDC_data/133.mat',
                                       n_clicks_timestamp='-1')),
                       html.Td(
                           html.Button('OR007at3_3', id='OR007at3_3', value='/home/david/Documents/BDC_data/147.mat',
                                       n_clicks_timestamp='-1')),
                       html.Td(
                           html.Button('OR007at12_3', id='OR007at12_3', value='/home/david/Documents/BDC_data/160.mat',
                                       n_clicks_timestamp='-1')),
                   ]
                   ),

               ]
               ),

    html.Div(id='output-mat-graphs'),
])


@app.callback(Output('output-mat-graphs', 'children'),
              [
                  Input('IR007_0', 'n_clicks_timestamp'),
                  Input('IR007_0', 'value'),
                  Input('B007_0', 'n_clicks_timestamp'),
                  Input('B007_0', 'value'),
                  Input('OR007at6_0', 'n_clicks_timestamp'),
                  Input('OR007at6_0', 'value'),
                  Input('OR007at3_0', 'n_clicks_timestamp'),
                  Input('OR007at3_0', 'value'),
                  Input('OR007at12_0', 'n_clicks_timestamp'),
                  Input('OR007at12_0', 'value'),
                  Input('IR007_1', 'n_clicks_timestamp'),
                  Input('IR007_1', 'value'),
                  Input('B007_1', 'n_clicks_timestamp'),
                  Input('B007_1', 'value'),
                  Input('OR007at6_1', 'n_clicks_timestamp'),
                  Input('OR007at6_1', 'value'),
                  Input('OR007at3_1', 'n_clicks_timestamp'),
                  Input('OR007at3_1', 'value'),
                  Input('OR007at12_1', 'n_clicks_timestamp'),
                  Input('OR007at12_1', 'value'),
                  Input('IR007_2', 'n_clicks_timestamp'),
                  Input('IR007_2', 'value'),
                  Input('B007_2', 'n_clicks_timestamp'),
                  Input('B007_2', 'value'),
                  Input('OR007at6_2', 'n_clicks_timestamp'),
                  Input('OR007at6_2', 'value'),
                  Input('OR007at3_2', 'n_clicks_timestamp'),
                  Input('OR007at3_2', 'value'),
                  Input('OR007at12_2', 'n_clicks_timestamp'),
                  Input('OR007at12_2', 'value'),
                  Input('IR007_3', 'n_clicks_timestamp'),
                  Input('IR007_3', 'value'),
                  Input('B007_3', 'n_clicks_timestamp'),
                  Input('B007_3', 'value'),
                  Input('OR007at6_3', 'n_clicks_timestamp'),
                  Input('OR007at6_3', 'value'),
                  Input('OR007at3_3', 'n_clicks_timestamp'),
                  Input('OR007at3_3', 'value'),
                  Input('OR007at12_3', 'n_clicks_timestamp'),
                  Input('OR007at12_3', 'value'),
              ], )
def update_output(t1, v1,
                  t2, v2,
                  t3, v3,
                  t4, v4,
                  t5, v5,
                  t6, v6,
                  t7, v7,
                  t8, v8,
                  t9, v9,
                  t10, tv0,
                  t11, tv1,
                  t12, tv2,
                  t13, tv3,
                  t14, tv4,
                  t15, v15,
                  t16, v16,
                  t17, v17,
                  t18, v18,
                  t19, v19,
                  t20, v20,
                  ):
    # return html.H5('asa')
    params = []
    for a in locals().values():
        params.append(a)
    ts = []
    vs = []
    for param in params:
        if isinstance(param, list):
            continue
        if params.index(param) % 2 == 0:
            if param is None:
                ts.append(-1)
            else:
                ts.append(int(param))
        else:
            vs.append(param)

    t = np.max(ts)
    if t is not None:
        return plot(vs[ts.index(t)])


if __name__ == '__main__':
    mat_contents = sio.loadmat('/home/david/Documents/BDC_data/109.mat', squeeze_me=True)

    for key in mat_contents:
        if key[:2] != "__" and key[-3:] != "RPM":
            print(key)
            # for x in mat_contents[key]:
            #     print(x)
