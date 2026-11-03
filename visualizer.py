"""
Graph Visualizer on its own: the files saved by the program viewed without
the instrument, nor pyvisa. The main window opens the same window from
Utility > Graph Visualizer.
"""
from PyQt6.QtWidgets import QApplication
from Fluke8588A.controllers.graph_visualizer_controller import GraphVisualizerController
from Fluke8588A.views.graph_visualizer import GraphVisualizerWindow
import logging
import sys


def main():
    # Ω/μ in the messages: escaped on a cp1252 output, as in main.py
    for stream in (sys.stdout, sys.stderr):
        if stream is not None:  # None with pythonw
            stream.reconfigure(errors="backslashreplace")
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    app = QApplication(sys.argv)
    visualizer = GraphVisualizerController(GraphVisualizerWindow())
    visualizer.show_window()
    app.exec()


if __name__ == "__main__":
    main()
