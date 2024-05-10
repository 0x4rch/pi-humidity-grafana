import time
import os
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv
import adafruit_dht
from sensor import Sensor

load_dotenv()  # take environment variables from .env.

token = os.environ.get("INFLUXDB_TOKEN")
org = os.environ.get("org")
url = os.environ.get("url")
bucket = os.environ.get("bucket")
client = InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

sensor = Sensor(board.D4)

while True:
    temperature_f, humidity = sensor.read_data()
    if temperature_f is not None and humidity is not None:
        point = Point("temp_f").field("temp_f", temperature_f)
        write_api.write(bucket=bucket, org="Traphouse", record=point)
        point = Point("humidity_percent").field("humidity_percent", humidity)
        write_api.write(bucket=bucket, org="Traphouse", record=point)
    time.sleep(2.0)
