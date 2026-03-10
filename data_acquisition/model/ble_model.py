from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from typing import Callable

from bleak import BleakClient, BleakScanner


@dataclass(frozen=True)
class DiscoveredDevice:
    name: str
    address: str
    rssi: int | None


NotifyCallback = Callable[[bytes], None]


class BleDeviceModel:
    def __init__(self) -> None:
        self._client: BleakClient | None = None
        self._connected_address: str | None = None

    @property
    def is_connected(self) -> bool:
        return bool(self._client and self._client.is_connected)

    @property
    def connected_address(self) -> str | None:
        return self._connected_address

    async def scan(self, timeout_s: float = 5.0) -> list[DiscoveredDevice]:
        # Create a scanner instance so we can stop it cleanly when the loop goes away.
        scanner = BleakScanner()
        try:
            await scanner.start()
            await asyncio.sleep(timeout_s)
            devices = list(scanner.discovered_devices)
        finally:
            with contextlib.suppress(Exception):
                await scanner.stop()
        results: list[DiscoveredDevice] = []
        for d in devices:
            results.append(
                DiscoveredDevice(
                    name=d.name or "",
                    address=d.address,
                    rssi=getattr(d, "rssi", None),
                )
            )
        results.sort(key=lambda x: (x.name.lower(), x.address))
        return results

    async def connect(
        self,
        address: str,
        disconnected_cb: Callable[[], None] | None = None,
    ) -> None:
        await self.disconnect()

        client = BleakClient(address, disconnected_callback=(lambda _c: disconnected_cb() if disconnected_cb else None))
        await client.connect()
        self._client = client
        self._connected_address = address

    async def start_notify(self, char_uuid: str, callback: NotifyCallback) -> None:
        if not self._client:
            raise RuntimeError("Not connected")

        def _cb(_sender: int, data: bytearray) -> None:
            callback(bytes(data))

        await self._client.start_notify(char_uuid, _cb)

    async def stop_notify(self, char_uuid: str) -> None:
        if self._client and self._client.is_connected:
            await self._client.stop_notify(char_uuid)

    async def disconnect(self) -> None:
        if self._client:
            try:
                if self._client.is_connected:
                    await self._client.disconnect()
            finally:
                self._client = None
                self._connected_address = None

