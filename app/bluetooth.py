import js
import pyodide

ID_SERVICE = "48c5d828-ac2a-442d-97a3-0c9822b04979"
UART_SERVICE = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
TX_CHARACTERISTIC = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
RX_CHARACTERISTIC = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"


class Bluetooth:
    def __init__(self):
        self.device = None
        self.gatt = None
        self.disconnected_callback = None
        self.data_received_callback = None
        self.uart_service = None
        self.tx_characteristic = None
        self.rx_characteristic = None

    async def connect(self):
        if self.is_connected():
            return

        scan_options = {
            "filters": [{"services": [ID_SERVICE]}],
            "optionalServices": [UART_SERVICE],
        }
        self.device = await js.navigator.bluetooth.requestDevice(
            pyodide.to_js(scan_options, dict_converter=js.Object.fromEntries)
        )
        self.device.addEventListener(
            "gattserverdisconnected", lambda event: self._disconnected()
        )
        self.gatt = await self.device.gatt.connect()
        self.uart_service = await self.gatt.getPrimaryService(UART_SERVICE)
        self.tx_characteristic = await self.uart_service.getCharacteristic(
            TX_CHARACTERISTIC
        )
        self.rx_characteristic = await self.uart_service.getCharacteristic(
            RX_CHARACTERISTIC
        )
        await self.rx_characteristic.startNotifications()
        self.rx_characteristic.addEventListener(
            "characteristicvaluechanged", self._data_received
        )

    def is_connected(self):
        return bool(self.device and self.gatt and self.gatt.connected)

    def _disconnected(self):
        self.device = None
        self.gatt = None
        self.uart_service = None
        self.tx_characteristic = None
        self.rx_characteristic = None
        if self.disconnected_callback:
            self.disconnected_callback()

    def _data_received(self, event):
        data = event.target.value.buffer.to_py().tobytes()
        if self.data_received_callback:
            self.data_received_callback(data)

    def disconnect(self):
        if self.is_connected():
            self.gatt.disconnect()

    async def write(self, data):
        if self.is_connected():
            await self.tx_characteristic.writeValueWithResponse(pyodide.to_js(data))
