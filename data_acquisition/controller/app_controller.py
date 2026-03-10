from __future__ import annotations

import asyncio
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from PySide6 import QtCore

from ..constants import LHM_NOTIFY_CHAR_UUID
from ..model.ble_model import BleDeviceModel, DiscoveredDevice
from ..model.data_store import SessionDataStore
from ..model.parser import parse_lahmo2_csv_line
from ..model.types import Sample
from ..view.main_window import DeviceRow, MainWindow


@dataclass(frozen=True)
class PlotBuffers:
    x_ms: deque[float]
    pv0_mv: deque[float]
    pv1_mv: deque[float]
    pv2_mv: deque[float]
    pv3_mv: deque[float]
    roll: deque[float]
    pitch: deque[float]
    yaw: deque[float]


class AppController(QtCore.QObject):
    def __init__(
        self,
        view: MainWindow,
        ble: BleDeviceModel,
        store: SessionDataStore,
        max_len: int = 300,
        refresh_hz: float = 20.0,
    ) -> None:
        super().__init__()
        self._view = view
        self._ble = ble
        self._store = store
        self._notify_char_uuid = LHM_NOTIFY_CHAR_UUID

        self._buffers = PlotBuffers(
            x_ms=deque(maxlen=max_len),
            pv0_mv=deque(maxlen=max_len),
            pv1_mv=deque(maxlen=max_len),
            pv2_mv=deque(maxlen=max_len),
            pv3_mv=deque(maxlen=max_len),
            roll=deque(maxlen=max_len),
            pitch=deque(maxlen=max_len),
            yaw=deque(maxlen=max_len),
        )

        self._timer = QtCore.QTimer()
        self._timer.setInterval(int(1000 / refresh_hz))
        self._timer.timeout.connect(self._refresh_plots)

        self._wire()

    def _wire(self) -> None:
        self._view.scan_requested.connect(lambda: asyncio.create_task(self.scan()))
        self._view.connect_requested.connect(lambda addr: asyncio.create_task(self.connect(addr)))
        self._view.disconnect_requested.connect(lambda: asyncio.create_task(self.disconnect()))

    async def scan(self) -> None:
        try:
            devices = await self._ble.scan(timeout_s=5.0)
        except Exception as exc:
            self._view._set_status(f"Status: scan failed: {exc}")
            return
        name_filter = self._view.device_name_edit.text().strip().lower()
        addr_filter = self._view.address_edit.text().strip().lower()

        rows: list[DeviceRow] = []
        for d in devices:
            if name_filter and name_filter not in (d.name or "").lower():
                continue
            if addr_filter and addr_filter not in d.address.lower():
                continue
            rows.append(DeviceRow(name=d.name, address=d.address, rssi=d.rssi))
        self._view.set_devices(rows)

    async def connect(self, address: str) -> None:
        self._notify_char_uuid = self._view.char_uuid_edit.text().strip() or LHM_NOTIFY_CHAR_UUID

        def on_disconnected() -> None:
            QtCore.QMetaObject.invokeMethod(self, "_on_disconnected_from_ble", QtCore.Qt.QueuedConnection)

        try:
            await self._ble.connect(address, disconnected_cb=on_disconnected)
            self._view.set_connected(True, address=address)

            # Start session logging
            label = self._view.device_name_edit.text().strip() or address
            path = self._store.start_session(device_label=label)
            self._view.set_session_path(str(path))

            self._clear_buffers()
            self._timer.start()

            await self._ble.start_notify(self._notify_char_uuid, self._on_notify_bytes)
        except Exception as exc:
            # Gracefully handle UUID / notify errors and show in status bar.
            self._timer.stop()
            self._store.stop_session()
            self._view.set_session_path("(not started)")
            self._view.set_connected(False)
            self._view._set_status(f"Status: connect failed: {exc}")

    @QtCore.Slot()
    def _on_disconnected_from_ble(self) -> None:
        self._timer.stop()
        self._store.stop_session()
        self._view.set_session_path("(not started)")
        self._view.set_connected(False)

    async def disconnect(self) -> None:
        try:
            await self._ble.stop_notify(self._notify_char_uuid)
        except Exception:
            # ignore stop-notify failures during disconnect
            pass
        await self._ble.disconnect()
        self._timer.stop()
        self._store.stop_session()
        self._view.set_session_path("(not started)")
        self._view.set_connected(False)

    def _on_notify_bytes(self, data: bytes) -> None:
        try:
            line = data.decode("utf-8", errors="ignore")
        except Exception:
            return
        sample = parse_lahmo2_csv_line(line)
        if not sample:
            return
        self._append_sample(sample)
        self._store.append(sample)

    def _append_sample(self, s: Sample) -> None:
        self._buffers.x_ms.append(float(s.timestamp_ms))
        self._buffers.pv0_mv.append(float(s.pv0_v) * 1000.0)
        self._buffers.pv1_mv.append(float(s.pv1_v) * 1000.0)
        self._buffers.pv2_mv.append(float(s.pv2_v) * 1000.0)
        self._buffers.pv3_mv.append(float(s.pv3_v) * 1000.0)
        self._buffers.roll.append(float(s.roll_deg))
        self._buffers.pitch.append(float(s.pitch_deg))
        self._buffers.yaw.append(float(s.yaw_deg))

    def _clear_buffers(self) -> None:
        for dq in (
            self._buffers.x_ms,
            self._buffers.pv0_mv,
            self._buffers.pv1_mv,
            self._buffers.pv2_mv,
            self._buffers.pv3_mv,
            self._buffers.roll,
            self._buffers.pitch,
            self._buffers.yaw,
        ):
            dq.clear()

    def _refresh_plots(self) -> None:
        x = list(self._buffers.x_ms)
        series = [
            list(self._buffers.pv0_mv),
            list(self._buffers.pv1_mv),
            list(self._buffers.pv2_mv),
            list(self._buffers.pv3_mv),
            list(self._buffers.roll),
            list(self._buffers.pitch),
            list(self._buffers.yaw),
        ]
        self._view.update_plots(x, series)

