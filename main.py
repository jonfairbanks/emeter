import asyncio
import os

from datetime import datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from kasa import SmartPlug

DEVICE = "pi-zero-w2"
DEBUG = os.getenv("DEBUG")
HOST = "https://us-central1-1.gcp.cloud2.influxdata.com"
TOKEN = os.getenv("INFLUX_TOKEN")
ORG = "fairplay89@gmail.com"
BUCKET = "power-usage"


async def main():
    dev = SmartPlug("192.168.4.68")
    client = InfluxDBClient(url=HOST, token=TOKEN, org=ORG)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    while True:
        await dev.update()  # Request an update

        watts = dev.emeter_realtime.power
        volts = dev.emeter_realtime.voltage
        amps = dev.emeter_realtime.current
        milliamps = dev.emeter_realtime.current * 1000
        total = dev.emeter_realtime.total

        if DEBUG:
            os.system('clear||cls')
            print("-- EMeter --")
            print(watts, "watts")
            print(volts, "volts")
            print(amps, "amps")
            print(milliamps, "milliamps")
            print(total, "kWh")

        # Write data to InfluxDB
        POINT = Point("power_usage") \
            .tag("device", DEVICE) \
            .field("watts", watts) \
            .field("volts", volts) \
            .field("amps", amps) \
            .field("milliamps", milliamps) \
            .field("total", total) \
            .time(datetime.utcnow(), WritePrecision.NS)
        write_api.write(bucket=BUCKET, record=POINT)

        await asyncio.sleep(0.25)  # Pause between updates

if __name__ == "__main__":
    print("EMeter is running...")
    asyncio.run(main())
