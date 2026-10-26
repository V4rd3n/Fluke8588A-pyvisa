from PyQt6.QtWidgets import QApplication
from Fluke8588A.controllers.app_controller import AppController
import logging
import sys

def main():
    # Debug messages hold Ω/μ: on a cp1252 output (redirected or piped) they would
    # raise inside a Qt slot and close the app, so unencodable characters are escaped
    for stream in (sys.stdout, sys.stderr):
        if stream is not None:  # None with pythonw
            stream.reconfigure(errors="backslashreplace")
    # INFO for everything, DEBUG only for the package: PyQt6.uic and pyvisa
    # would flood the output at DEBUG
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("Fluke8588A").setLevel(
        logging.DEBUG if AppController.TEST_MODE else logging.INFO
    )
    app = QApplication(sys.argv)
    app_controller = AppController()
    app.exec()


if __name__ == "__main__":
    main()
