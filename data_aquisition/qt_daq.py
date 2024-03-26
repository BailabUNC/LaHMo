import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QListWidget, QTextEdit
from PyQt5.QtBluetooth import QBluetoothDeviceDiscoveryAgent, QLowEnergyController, QBluetoothUuid, QLowEnergyService
from PyQt5.QtCore import Qt, pyqtSignal, QByteArray

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

LHM_DEVICE_NAME  = 'LHM_Yihan'
LHM_SERVICE_UUID = '12fb95d1-4954-450f-a82b-802f71541562'
LHM_CHAR_UUID    = '67136980-20d0-4711-8b37-3acd0fec8e7f'

class LHMReceiver(QMainWindow):
    
    # A custom signal for emitting received data
    dataReceived = pyqtSignal(str)

    def __init__(self):
        '''
        Initialize the UI and the BLE device discovery agent.
        '''
        super().__init__()
        self.initUI()
        self.deviceDiscoveryAgent = QBluetoothDeviceDiscoveryAgent()
        self.deviceDiscoveryAgent.deviceDiscovered.connect(self.addDevice)
        self.devices = []

    def initUI(self):
        '''
        Sets up the GUI, including a button for starting the scan and a list widget for displaying discovered devices.
        '''
        self.setWindowTitle('Device scanner')
        self.setGeometry(100, 100, 800, 800)

        layout = QVBoxLayout()

        # Scan button
        self.scanButton = QPushButton('Start scanning')
        self.scanButton.clicked.connect(self.startScan)
        layout.addWidget(self.scanButton)
        
        # Stop scan button
        self.stopScanButton = QPushButton('Stop scanning')
        self.stopScanButton.clicked.connect(self.stopScan)
        self.stopScanButton.setEnabled(False)
        layout.addWidget(self.stopScanButton)

        # Devices list
        self.devicesListWidget = QListWidget()
        self.devicesListWidget.itemClicked.connect(self.connectToDevice)
        layout.addWidget(self.devicesListWidget)
        
        centralWidget = QWidget()
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)

        self.dataDisplay = QTextEdit()
        self.dataDisplay.setReadOnly(True)
        layout.addWidget(self.dataDisplay)
        self.dataReceived.connect(self.updateDataDisplay)

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)

    def startScan(self):
        '''
        Clears the current device list and starts a new Bluetooth device discovery.
        '''
        self.devices.clear()
        self.devicesListWidget.clear()
        self.deviceDiscoveryAgent.start()
        self.scanButton.setEnabled(False)
        self.stopScanButton.setEnabled(True)

    def stopScan(self):
        self.deviceDiscoveryAgent.stop()
        self.scanButton.setEnabled(True)
        self.stopScanButton.setEnabled(False)

    def addDevice(self, device):
        '''
        Adds a discovered device to the list and updates the list widget.
        '''
        if device not in self.devices:
            self.devices.append(device)
            listItem = device.name() + ' [' + device.address().toString() + ']'
            self.devicesListWidget.addItem(listItem)

    def connectToDevice(self, listItem):
        '''
        Handles the connection to a selected device from the list.
        '''
        deviceInfo = listItem.text().split('[')[-1].split(']')[0]
        for device in self.devices:
            if device.address().toString() == deviceInfo:
                self.controller = QLowEnergyController.createCentral(device)
                self.controller.connected.connect(self.deviceConnected)
                self.controller.disconnected.connect(self.deviceDisconnected)
                self.controller.error.connect(self.controllerError)
                self.controller.serviceDiscovered.connect(self.serviceDiscovered)
                self.controller.discoveryFinished.connect(self.discoveryFinished)
                self.controller.connectToDevice()
                break

    '''
    Device connection and discovery
    '''

    def deviceConnected(self):
        '''
        Invoked when a device is connected; starts service discovery.
        '''
        print('Device connected. Discovering services...')
        self.controller.discoverServices()

    def deviceDisconnected(self):
        '''
        Invoked when the device is disconnected.
        '''
        try:
            print('Device connected. Discovering services...')
            self.controller.discoverServices()
        except Exception as e:
            print(f"Error in deviceConnected: {e}")

    def controllerError(self, error):
        '''
        Handles controller errors.
        '''
        print(f'Controller Error: {error}')

    def serviceDiscovered(self, srvUuid):
        '''
        Reports discovered services.
        '''
        print(f'Service discovered: {srvUuid.toString()}')

    def discoveryFinished(self):
        '''
        Indicates the end of service discovery.
        '''
        print('Service discovery finished.')
        lhm_service_uuid = QBluetoothUuid(LHM_SERVICE_UUID)
        self.targetService = self.controller.createServiceObject(lhm_service_uuid)
        if self.targetService:
            self.targetService.stateChanged.connect(self.serviceStateChanged)
            self.targetService.characteristicChanged.connect(self.characteristicChanged)
            self.targetService.descriptorWritten.connect(self.descriptorWritten)
            self.targetService.discoverDetails()
        else:
            print('LHM Service not found.')
    
    def serviceStateChanged(self, newState):
        if newState == QLowEnergyService.ServiceState.ServiceDiscovered:
            lhm_char_uuid = QBluetoothUuid(LHM_CHAR_UUID)
            self.lhm_char = self.targetService.characteristic(lhm_char_uuid)
            if self.lhm_char.isValid():
                self.targetService.readCharacteristic(self.lhm_char)
                self.targetService.writeDescriptor(self.lhm_char.descriptor(QBluetoothUuid.DescriptorType.ClientCharacteristicConfiguration),
                                                   QByteArray([0x01, 0x00]))
            else:
                print('Characteristic not found')

    def characteristicChanged(self, char, value):
        data = value.data.decode()
        self.dataReceived.emit(data)

    def descriptorWritten(self, descriptor, newValue):
        print('Descriptor written.')

    '''
    Data display
    '''
    def updateDataDisplay(self, data):
        try:
            split_data = data.split('\t')

            timestamp = int(split_data[0])
            photovoltage0 = float(split_data[1])
            photovoltage1 = float(split_data[2])
            photovoltage2 = float(split_data[3])
            photovoltage3 = float(split_data[4])
            roll = float(split_data[5])
            pitch = float(split_data[6])
            yaw = float(split_data[7])

            display_text = f'Timestamp: {timestamp}, PV0: {photovoltage0}, PV1: {photovoltage1}, PV2: {photovoltage2}, PV3: {photovoltage3}, Roll: {roll}, Pitch: {pitch}, Yaw: {yaw}'
            self.dataDisplay.append(display_text)

        except ValueError:
            print('Error parsing data: ', data)

        except IndexError:
            print('Incomplete data received: ', data)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    lhm_receiver = LHMReceiver()
    lhm_receiver.show()
    sys.exit(app.exec_())