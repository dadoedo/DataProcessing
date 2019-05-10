import dash_core_components as dcc
import dash_html_components as html
import MySQLdb

from app import configInfo

conn_get = MySQLdb.connect(host=configInfo["DATABASE"]["host"], user=configInfo["DATABASE"]["username"],
                           passwd=configInfo["DATABASE"]["password"], db=configInfo["DATABASE"]["database"])
cursor = conn_get.cursor()

cursor.execute("SELECT name, id FROM device")
rows = cursor.fetchall()
children = [html.H2('Monitored Devices', style={'textAlign': 'center'})]
for row in rows:
    children.append(html.H6("{}".format(row[0]), style={'margin-left': '35px'}))
    children.append(dcc.Link("Batch processing", href="/device/history/{}".format(row[1]),
                             style={'margin-left': '75px'}))
    children.append(html.Br())
    children.append(dcc.Link("Real Time processing", href="/device/realtime/{}".format(row[1]),
                             style={'margin-left': '75px'}))
    children.append(html.Br())
    children.append(html.Br())

layout = html.Div(children=children, style={'margin-left': '35px'})

