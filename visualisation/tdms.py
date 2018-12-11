import ntpath

from tdms_processing import tdms_files
from nptdms import TdmsFile
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State, Event
from app import app
from visualisation import mat

layout = html.Div(children=[
    html.H2(
        children='4dot raw Data',
        style={
            'textAlign': 'center',
        }
    ),
    dcc.Link('Home', href='/', style={'textAlign': 'right'}),
    html.Label('Dropdown'),
    dcc.Dropdown(id='filename_dropdown',
                 options=
                 tdms_files.generate_dropdown_inputs('/home/david/Documents/4dot_data/example_data', 'tdms'),
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
        children = [html.H3('File = {}'.format(ntpath.basename(path).split('.')[0]), style={'textAlign': 'center'})]
        for g in tdms_file.groups():
            for c in tdms_file.group_channels(g):
                if c.channel is not '0':
                    children.append(mat.plot_graph(c.data, 'Sensor {}'.format(c.channel)))

        return children
