from Fluke8588A.services import allan
from PyQt6.QtCore import QThread, pyqtSignal
class AllanThread(QThread):
    # Taus (s), Allan deviations (unit of the readings) and number of readings;
    # empty arrays when there are too few readings
    allan_ready = pyqtSignal(object, object, int)
    allan_failed = pyqtSignal(str)
    def __init__(self, load):
        """load() returns (times, values) of the readings, called in the thread (e.g. a file read)."""
        super().__init__()
        self._load = load

    def run(self):
        # One allantools call: it cannot be interrupted, a result no longer
        # wanted is discarded by whoever receives it
        try:
            times, values = self._load()
            taus, adevs = allan.overlapping_adev(values, allan.mean_rate(times))
        except Exception as error:
            self.allan_failed.emit(str(error))
            return
        self.allan_ready.emit(taus, adevs, len(values))
