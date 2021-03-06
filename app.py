import configparser
import dash
import MySQLdb


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# server = app.server
app.config.suppress_callback_exceptions = True

configInfo = configparser.ConfigParser()
configInfo.read('config.ini')

conn_get = MySQLdb.connect(host=configInfo["DATABASE"]["host"], user=configInfo["DATABASE"]["username"],
                           passwd=configInfo["DATABASE"]["password"], db=configInfo["DATABASE"]["database"])
cursor = conn_get.cursor()

controllerObjects = []

cursor.execute("SELECT id FROM device")
for row in cursor.fetchall():
    deviceId = row[0]
    controllerObjects.append({"id": deviceId, "object": None})
