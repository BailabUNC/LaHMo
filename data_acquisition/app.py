from __future__ import annotations

import asyncio
from pathlib import Path

from PySide6 import QtWidgets
from qasync import QEventLoop

from .controller.app_controller import AppController
from .model.ble_model import BleDeviceModel
from .model.data_store import SessionDataStore
from .view.main_window import MainWindow


def main() -> int:
    app = QtWidgets.QApplication([])
    app.setApplicationName("LaHMo BLE DAQ")

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    view = MainWindow()
    ble = BleDeviceModel()
    store_root = Path(__file__).resolve().parents[1] / "data_storage"
    store = SessionDataStore(store_root)
    _controller = AppController(view=view, ble=ble, store=store)

    view.show()
    with loop:
        loop.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

