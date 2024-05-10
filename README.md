# pi-humidity-grafana
Connect a Raspberry Pi with a DHT22 humidity & temperature sensor to InfluxDB and then to Grafana

### Pinout
![image](https://github.com/0x4rch/pi-humidity-grafana/assets/6191866/05db6ad5-af5c-4bac-a00d-cc4c30c6aed4)
> Taken from https://tutorials-raspberrypi.com/raspberry-pi-measure-humidity-temperature-dht11-dht22/

### .ENV
For credentails create a .env in the directory with the following vars:
```bash
INFLUXDB_TOKEN="" # Influx API Token
org="" # Influx Organization
url="" # Influx DB URL
bucket="" # Influx Bucket
```
### Service
- Service file should live at `lib/systemd/system/pi-humidity-grafana.service`
- To pick up the new service `sudo systemctl daemon-reload`
- To enable the service at startup `sudo systemctl enable pi-humidity-grafana.service`
- To start manually `sudo systemctl start pi-humidity-grafana.service`

### Display
We also support a 16x2 lcd display check out Display.py for info
