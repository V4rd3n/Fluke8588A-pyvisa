from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTabWidget
import os
trigger_window_loc = os.path.join(os.path.dirname(__file__), "ui", "trigger.ui")

class TriggerWindow(QTabWidget):
    def __init__(self):
        super().__init__()
        uic.load_ui(trigger_window_loc)
    