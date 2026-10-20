import asyncio
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from kasa import Module
from kasa.iot.modules.emeter import Emeter

import main


class EnergyFieldsTests(unittest.TestCase):
    def energy(self, realtime):
        now = datetime.now()
        data = {
            "get_realtime": realtime,
            "get_daystat": {"day_list": [{"day": now.day, "energy_wh": 500}]},
            "get_monthstat": {
                "month_list": [{"month": now.month, "energy_wh": 2000}]
            },
        }

        class PayloadEmeter(Emeter):
            @property
            def data(self):
                return data

        return PayloadEmeter(Mock(), "emeter")

    def test_wire_units_preserve_metric_schema(self):
        payloads = [
            {"power_mw": 12345, "voltage_mv": 121148,
             "current_ma": 123, "total_wh": 4567},
            {"power": 12.345, "voltage": 121.148,
             "current": 0.123, "total": 4.567},
        ]
        expected = {"watts": 12.345, "volts": 121.148, "amps": 0.123,
                    "milliamps": 123.0, "total": 4.567,
                    "daily": 0.5, "monthly": 2.0}
        for payload in payloads:
            with self.subTest(payload=payload):
                self.assertEqual(
                    main.energy_fields(self.energy(payload)), expected
                )

    def test_zero_readings_are_preserved(self):
        fields = main.energy_fields(self.energy({
            "power_mw": 0, "voltage_mv": 0, "current_ma": 0, "total_wh": 0
        }))
        for name in ("watts", "volts", "amps", "milliamps", "total"):
            self.assertEqual(fields[name], 0.0)

    def test_missing_optional_readings_are_omitted(self):
        fields = main.energy_fields(self.energy({"power_mw": 1000}))
        self.assertEqual(fields, {"watts": 1.0, "daily": 0.5, "monthly": 2.0})

    def test_no_readings_raises(self):
        energy = SimpleNamespace(**{name: None for name in (
            "current_consumption", "voltage", "current", "consumption_total",
            "consumption_today", "consumption_this_month"
        )})
        with self.assertRaisesRegex(RuntimeError, "no energy readings"):
            main.energy_fields(energy)


class PollingTests(unittest.IsolatedAsyncioTestCase):
    async def run_poll(self, dev, client, sleep):
        with patch.object(main, "IotPlug", return_value=dev), \
                patch.object(main, "InfluxDBClient", return_value=client), \
                patch.object(main.asyncio, "sleep", sleep), \
                patch.object(main, "DEBUG", False), \
                patch.object(main, "DEVICE", "TestDevice"):
            await main.main()

    def devices(self):
        energy = SimpleNamespace(
            current_consumption=12.345, voltage=121.148, current=0.123,
            consumption_total=4.567, consumption_today=0.5,
            consumption_this_month=2.0
        )
        dev = Mock(modules={Module.Energy: energy})
        dev.update = AsyncMock()
        dev.disconnect = AsyncMock()
        client = Mock()
        client.__enter__ = Mock(return_value=client)
        client.__exit__ = Mock(return_value=False)
        return dev, client

    async def test_poll_writes_expected_fields_and_closes_on_cancel(self):
        dev, client = self.devices()
        with self.assertRaises(asyncio.CancelledError):
            await self.run_poll(dev, client, AsyncMock(
                side_effect=asyncio.CancelledError
            ))
        dev.update.assert_awaited_once()
        write = client.write_api.return_value.write
        write.assert_called_once()
        self.assertEqual(write.call_args.kwargs["bucket"], main.BUCKET)
        record = write.call_args.kwargs["record"]
        line = record.to_line_protocol()
        self.assertTrue(line.startswith("power_usage,device=TestDevice "))
        fields = line.split(" ")[1]
        self.assertEqual(set(fields.split(",")), {
            "amps=0.123", "daily=0.5", "milliamps=123", "monthly=2",
            "total=4.567", "volts=121.148", "watts=12.345"
        })
        dev.disconnect.assert_awaited_once()
        client.__exit__.assert_called_once()

    async def test_unsupported_plug_does_not_write(self):
        dev, client = self.devices()
        dev.modules = {}
        with self.assertRaisesRegex(RuntimeError, "does not support energy"):
            await self.run_poll(dev, client, AsyncMock())
        client.write_api.return_value.write.assert_not_called()
        dev.disconnect.assert_awaited_once()
        client.__exit__.assert_called_once()

    async def test_update_failure_closes_resources(self):
        dev, client = self.devices()
        dev.update.side_effect = TimeoutError("Plug timed out")
        with self.assertRaises(TimeoutError):
            await self.run_poll(dev, client, AsyncMock())
        client.write_api.return_value.write.assert_not_called()
        dev.disconnect.assert_awaited_once()
        client.__exit__.assert_called_once()

    async def test_write_failure_closes_resources(self):
        dev, client = self.devices()
        client.write_api.return_value.write.side_effect = OSError(
            "Write failed"
        )
        with self.assertRaises(OSError):
            await self.run_poll(dev, client, AsyncMock())
        dev.disconnect.assert_awaited_once()
        client.__exit__.assert_called_once()
