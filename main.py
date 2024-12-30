import time
import os
import board
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv
import adafruit_dht
from sensor import Sensor
from display import Display
from camera import CameraStream

load_dotenv()  # take environment variables from .env.

token = os.environ.get("INFLUXDB_TOKEN")
org = os.environ.get("org")
url = os.environ.get("url")
bucket = os.environ.get("bucket")
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

sensor = Sensor(board.D4)
display = Display()
temperature_f, humidity = sensor.read_data()

app = CameraStream(1280, 720, temperature_f, humidity)
# Start the app in a separate thread
app_thread = threading.Thread(target=app.start)
app_thread.daemon = True  # Make sure the thread exits when the main program exits
app_thread.start()

while True:
    temperature_f, humidity = sensor.read_data()
    if temperature_f is not None and humidity is not None:
        app.update_temperature_and_humidity(temperature_f, humidity)
        point = Point("temp_f").field("temp_f", temperature_f)
        write_api.write(bucket=bucket, org="Traphouse", record=point)
        point = Point("humidity_percent").field("humidity_percent", humidity)
        write_api.write(bucket=bucket, org="Traphouse", record=point)
        display.print_message(humidity, temperature_f)
    time.sleep(2.0)
