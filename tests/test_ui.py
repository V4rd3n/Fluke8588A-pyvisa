from PyQt6 import QtWidgets, uic
import sys

# You need one (and only one) QApplication instance per application.
# Pass in sys.argv to allow command line arguments for your app.
# If you know you won't use command line arguments QApplication([]) works too.
app = QtWidgets.QApplication(sys.argv)

window = uic.loadUi(".\\new_ui\\new_main_window.ui")
window.show()  # IMPORTANT!!!!! Windows are hidden by default.

# Start the event loop.
app.exec()