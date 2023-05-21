# pi-humidity-grafana
raspberry pi dht22 grafana

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
