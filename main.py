from PyQt6.QtWidgets import QApplication
from src.Fluke8588A.controllers.app_controller import AppController
import sys

def main():
    app = QApplication(sys.argv)
    app_controller = AppController()
    app.exec()


if __name__ == "__main__":
    main()