import dash_core_components as dcc
import dash_html_components as html
import MySQLdb


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


conn_get = MySQLdb.connect(host="172.16.23.204", user="fourdot", passwd="4d0tFourdot", db="dp")
cursor = conn_get.cursor()
cursor.execute("SELECT name, id FROM device")
rows = cursor.fetchall()
children = [html.H2('Monitored Devices', style={'textAlign': 'center'})]
for row in rows:
    children.append(html.H6("{}".format(row[0]), style={'margin-left': '35px'}))
    children.append(dcc.Link("Overlook/history", href="/device/history/{}".format(row[1]),
                             style={'margin-left': '75px'}))
    children.append(html.Br())
    children.append(dcc.Link("Real Time", href="/device/realtime/{}".format(row[1]),
                             style={'margin-left': '75px'}))
    children.append(html.Br())
    children.append(html.Br())

layout = html.Div(children=children, style={'margin-left': '35px'})
