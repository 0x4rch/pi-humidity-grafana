# Taken From https://tutorials-raspberrypi.com/raspberry-pi-measure-humidity-temperature-dht11-dht22/
import time
import adafruit_dht
from dotenv import load_dotenv

class Sensor:
    def __init__(self, pin):
        self.dhtDevice = adafruit_dht.DHT22(pin)

    def read_data(self):
        try:
            temperature_c = self.dhtDevice.temperature
            temperature_f = temperature_c * (9 / 5) + 32
            humidity = self.dhtDevice.humidity
            return temperature_f, humidity
        except RuntimeError as error:
            # Errors happen fairly often, DHT's are hard to read, just keep going
            time.sleep(2.0)
            return None, None
        except Exception as error:
            self.dhtDevice.exit()
            raise error
