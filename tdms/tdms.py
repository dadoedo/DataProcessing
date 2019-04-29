import glob
import ntpath

from nptdms import TdmsFile
import json
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from app import app


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
