import asyncio
import os

from datetime import UTC, datetime
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from kasa import Module
from kasa.iot import IotPlug

DEBUG = os.getenv("DEBUG", False)
DEVICE = os.getenv("DEVICE", "My Device")
PLUG = os.getenv("PLUG")
HOST = os.getenv("INFLUX_HOST", "https://us-central1-1.gcp.cloud2.influxdata.com")  # noqa
TOKEN = os.getenv("INFLUX_TOKEN")
ORG = os.getenv("INFLUX_ORG")
BUCKET = os.getenv("INFLUX_BUCKET", "power-usage")


def energy_fields(energy):
    """Read supported metrics in the existing InfluxDB units."""
    fields = {
        "watts": energy.current_consumption,
        "volts": energy.voltage,
        "amps": energy.current,
        "total": energy.consumption_total,
        "daily": energy.consumption_today,
        "monthly": energy.consumption_this_month,
    }
    if fields["amps"] is not None:
        fields["milliamps"] = fields["amps"] * 1000
    fields = {name: float(value) for name, value in fields.items()
              if value is not None}
    if not fields:
        raise RuntimeError("The plug returned no energy readings")
    return fields


async def main():
    dev = IotPlug(PLUG)
    try:
        with InfluxDBClient(url=HOST, token=TOKEN, org=ORG) as client:
            write_api = client.write_api(write_options=SYNCHRONOUS)
            while True:
                await dev.update()
                energy = dev.modules.get(Module.Energy)
                if energy is None:
                    raise RuntimeError(
                        "The plug does not support energy monitoring"
                    )
                fields = energy_fields(energy)

                if DEBUG:
                    os.system('clear||cls')
                    print("-- EMeter --")
                    for name, value in fields.items():
                        print(name, value)

                point = Point("power_usage").tag("device", DEVICE)
                for name, value in fields.items():
                    point.field(name, value)
                point.time(datetime.now(UTC), WritePrecision.NS)
                write_api.write(bucket=BUCKET, record=point)
                await asyncio.sleep(1)
    finally:
        await dev.disconnect()


if __name__ == "__main__":
    print("EMeter is running...")
    asyncio.run(main())
