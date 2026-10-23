from PyQt6 import uic
from PyQt6.QtWidgets import QWidget
import os


graph_window_loc = os.path.join(
    os.path.dirname(__file__), "..", "ui", "graph_window.ui"
)


class GraphWindow(QWidget):

    def __init__(self):
        super().__init__()
        uic.loadUi(graph_window_loc, self)
        self.setWindowTitle("Graph")

    def show_function(self, function: str):
        self.setWindowTitle(f"{function} Graph")
        self.show()
        self.raise_()
        self.activateWindow()
