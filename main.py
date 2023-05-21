# Taken From https://tutorials-raspberrypi.com/raspberry-pi-measure-humidity-temperature-dht11-dht22/
import time, board, adafruit_dht, influxdb_client, os
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.
 
dhtDevice = adafruit_dht.DHT22(board.D4)
token = os.environ.get("INFLUXDB_TOKEN")
org = os.environ.get("org")
url = os.environ.get("url")
bucket = os.environ.get("bucket")
client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
write_api = client.write_api(write_options=SYNCHRONOUS)

while True:
    try:
        temperature_c = dhtDevice.temperature
        temperature_f = temperature_c * (9 / 5) + 32
        humidity = dhtDevice.humidity
        point = Point("temp_f").field("temp_f", temperature_f)
        write_api.write(bucket=bucket, org="Traphouse", record=point)
        point = Point("humidity_percent").field("humidity_percent", humidity)
        write_api.write(bucket=bucket, org="Traphouse", record=point)
 
    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        time.sleep(2.0)
        continue
    except Exception as error:
        dhtDevice.exit()
        raise error
 
    time.sleep(2.0)

