from __future__ import annotations

from dataclasses import dataclass

from PySide6 import QtCore, QtGui, QtWidgets
import pyqtgraph as pg

from ..constants import LHM_DEFAULT_DEVICE_NAME, LHM_NOTIFY_CHAR_UUID, LHM_SERVICE_UUID


@dataclass(frozen=True)
class DeviceRow:
    name: str
    address: str
    rssi: int | None


class MainWindow(QtWidgets.QMainWindow):
    scan_requested = QtCore.Signal()
    connect_requested = QtCore.Signal(str)
    disconnect_requested = QtCore.Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LaHMo BLE DAQ")
        self.resize(1100, 750)

        self._build_ui()

    def _build_ui(self) -> None:
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)

        layout = QtWidgets.QHBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Left: device control panel
        left = QtWidgets.QFrame()
        left.setMinimumWidth(360)
        left.setMaximumWidth(420)
        left.setFrameShape(QtWidgets.QFrame.StyledPanel)
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setSpacing(10)

        title = QtWidgets.QLabel("BLE Devices")
        title_font = QtGui.QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        left_layout.addWidget(title)

        form = QtWidgets.QFormLayout()
        form.setLabelAlignment(QtCore.Qt.AlignLeft)

        self.device_name_edit = QtWidgets.QLineEdit(LHM_DEFAULT_DEVICE_NAME)
        self.device_name_edit.setPlaceholderText("Filter by name (optional)")
        form.addRow("Name filter", self.device_name_edit)

        self.address_edit = QtWidgets.QLineEdit("")
        self.address_edit.setPlaceholderText("Exact address / UUID (optional)")
        form.addRow("Address", self.address_edit)

        self.service_uuid_edit = QtWidgets.QLineEdit(LHM_SERVICE_UUID)
        self.service_uuid_edit.setPlaceholderText("Service UUID (optional)")
        form.addRow("Service UUID", self.service_uuid_edit)

        self.char_uuid_edit = QtWidgets.QLineEdit(LHM_NOTIFY_CHAR_UUID)
        self.char_uuid_edit.setPlaceholderText("Notify characteristic UUID")
        form.addRow("Notify char UUID", self.char_uuid_edit)

        left_layout.addLayout(form)

        btn_row = QtWidgets.QHBoxLayout()
        self.scan_btn = QtWidgets.QPushButton("Scan")
        self.connect_btn = QtWidgets.QPushButton("Connect")
        self.disconnect_btn = QtWidgets.QPushButton("Disconnect")
        self.disconnect_btn.setEnabled(False)

        btn_row.addWidget(self.scan_btn)
        btn_row.addWidget(self.connect_btn)
        btn_row.addWidget(self.disconnect_btn)
        left_layout.addLayout(btn_row)

        self.devices_list = QtWidgets.QListWidget()
        self.devices_list.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        left_layout.addWidget(self.devices_list, stretch=1)

        self.status_label = QtWidgets.QLabel("Status: idle")
        self.status_label.setWordWrap(True)
        left_layout.addWidget(self.status_label)

        self.session_path_label = QtWidgets.QLabel("Log: (not started)")
        self.session_path_label.setWordWrap(True)
        left_layout.addWidget(self.session_path_label)

        left_layout.addStretch(1)
        layout.addWidget(left)

        # Right: plots
        right = QtWidgets.QFrame()
        right.setFrameShape(QtWidgets.QFrame.StyledPanel)
        right_layout = QtWidgets.QVBoxLayout(right)

        pg.setConfigOptions(antialias=True)
        self.plot_widget = pg.GraphicsLayoutWidget()
        right_layout.addWidget(self.plot_widget, stretch=1)

        self._plots: list[pg.PlotItem] = []
        self._curves: list[pg.PlotDataItem] = []

        labels = [
            "PV0 (mV)",
            "PV1 (mV)",
            "PV2 (mV)",
            "PV3 (mV)",
            "Roll (deg)",
            "Pitch (deg)",
            "Yaw (deg)",
        ]

        for i, lab in enumerate(labels):
            p = self.plot_widget.addPlot(row=i, col=0)
            p.showGrid(x=True, y=True, alpha=0.25)
            p.setLabel("left", lab)
            if i == len(labels) - 1:
                p.setLabel("bottom", "Time (ms)")
            else:
                p.hideAxis("bottom")
            curve = p.plot([], [], pen=pg.mkPen(color=pg.intColor(i, hues=7), width=2))
            self._plots.append(p)
            self._curves.append(curve)

        layout.addWidget(right, stretch=1)

        # Wire UI events to signals
        self.scan_btn.clicked.connect(self.scan_requested.emit)
        self.disconnect_btn.clicked.connect(self.disconnect_requested.emit)
        self.connect_btn.clicked.connect(self._emit_connect_requested)
        self.devices_list.itemDoubleClicked.connect(lambda _item: self._emit_connect_requested())

    def _emit_connect_requested(self) -> None:
        addr = self.address_edit.text().strip()
        if not addr:
            item = self.devices_list.currentItem()
            if not item:
                self._set_status("Status: select a device or enter an address.")
                return
            addr = item.data(QtCore.Qt.UserRole)
        self.connect_requested.emit(addr)

    def set_devices(self, devices: list[DeviceRow]) -> None:
        self.devices_list.clear()
        for d in devices:
            rssi_str = f"{d.rssi} dBm" if d.rssi is not None else "n/a"
            name = d.name if d.name else "(no name)"
            item = QtWidgets.QListWidgetItem(f"{name}  |  {d.address}  |  RSSI: {rssi_str}")
            item.setData(QtCore.Qt.UserRole, d.address)
            self.devices_list.addItem(item)

    def set_connected(self, connected: bool, address: str | None = None) -> None:
        self.disconnect_btn.setEnabled(connected)
        self.connect_btn.setEnabled(not connected)
        self.scan_btn.setEnabled(not connected)
        if connected:
            self._set_status(f"Status: connected to {address}")
        else:
            self._set_status("Status: disconnected")

    def set_session_path(self, text: str) -> None:
        self.session_path_label.setText(f"Log: {text}")

    def update_plots(self, x_ms: list[float], series: list[list[float]]) -> None:
        # series must be length 7; each is y values aligned with x_ms
        for i in range(min(7, len(series))):
            self._curves[i].setData(x_ms, series[i])

    def _set_status(self, text: str) -> None:
        self.status_label.setText(text)

