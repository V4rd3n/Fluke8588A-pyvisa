from PyQt6.QtWidgets import QApplication
from Fluke8588A.controllers.app_controller import AppController
import sys

def main():
    # Debug prints hold Ω/μ: on a cp1252 output (redirected or piped) they would
    # raise inside a Qt slot and close the app, so unencodable characters are escaped
    for stream in (sys.stdout, sys.stderr):
        if stream is not None:  # None with pythonw
            stream.reconfigure(errors="backslashreplace")
    app = QApplication(sys.argv)
    app_controller = AppController()
    app.exec()


if __name__ == "__main__":
    main()