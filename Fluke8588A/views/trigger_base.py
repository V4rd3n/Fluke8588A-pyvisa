import os

from PyQt6 import uic
from PyQt6.QtWidgets import QWidget


trigger_base_window_loc = os.path.join(
    os.path.dirname(__file__), "..", "new_ui", "trigger_base.ui"
)


class TriggerBaseWindow(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi(trigger_base_window_loc, self)
        self.setWindowTitle("Base Trigger Settings")
