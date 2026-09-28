import pyvisa
from pathlib import Path
from PyQt6 import QtWidgets, uic
import sys

ROOT = Path(__file__).resolve().parents[1]
UI_FILE = ROOT / "new_ui" / "main_window.ui"

def _scan_devices():
    window.scan_combobox.clear()
    try:
        devices = rm.list_resources()
    except Exception as error:
        print(f"Could not scan VISA resources: {error}")
        window.scan_combobox.setEnabled(False)
        return

    print(f"VISA resources found: {devices}")
    if not devices:
        print("No VISA resources found")

    for device in devices:
        print(f"Querying {device}...")
        try:
            instr = rm.open_resource(device)
            try:
                response = instr.query("*IDN?")
                identity = [part.strip() for part in response.split(",")]
            finally:
                instr.close()
        except pyvisa.errors.VisaIOError as error:
            print(f"Could not read {device}: {error}")
            identity = ["No identification response"]
        dev = device.split("::")
        name = ", ".join(identity)
        name = name + " (" + dev[0].strip() + ")"
        window.scan_combobox.addItem(name, userData=device)
        print(f"{device}: {identity}")

    window.scan_combobox.setEnabled(bool(devices))
    window.connect_button.setEnabled(bool(devices))

def _connect():
    resource_name = window.scan_combobox.currentData()
    if not resource_name:
        print("No instrument selected")
        return

    try:
        window.instr = rm.open_resource(resource_name)
        window.instr.timeout = 5000
        if "SOCKET" in resource_name:
            window.instr.read_termination = "\n"
            window.instr.write_termination = "\n"
        print(f"Connected to {resource_name}")
        print(window.instr.query("*IDN?"))
        window.connect_button.setEnabled(False)
    except pyvisa.errors.VisaIOError as error:
        window.instr = None
        print(f"Could not connect to {resource_name}: {error}")


rm = pyvisa.ResourceManager()
app = QtWidgets.QApplication(sys.argv)
window = uic.loadUi(str(UI_FILE))
window.instr = None
window.scan_button.clicked.connect(_scan_devices)
window.connect_button.clicked.connect(_connect)


window.show()

app.exec()