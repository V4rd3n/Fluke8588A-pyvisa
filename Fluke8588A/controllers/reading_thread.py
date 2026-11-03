from PyQt6.QtCore import QThread, pyqtSignal
import time
class ReadingThread(QThread):
    # Primary text, secondary text (None when not read or not available) and
    # the PC time they arrived (time.perf_counter, s)
    reading_ready = pyqtSignal(str, object, float)
    reading_failed = pyqtSignal(str)
    def __init__(self, instr_ctrl, secondary: bool = False):
        super().__init__()
        self._instr_ctrl = instr_ctrl
        self._secondary = secondary
        self._running = False

    def run(self):
        self._running=True
        while self._running:
            try:
                if self._secondary:
                    value, secondary = self._instr_ctrl.read_with_secondary()
                else:
                    value, secondary = self._instr_ctrl.read(), None
            except Exception as error:
                self._running = False
                self.reading_failed.emit(str(error))
                return
            if secondary is not None:
                secondary = secondary.strip()
            self.reading_ready.emit(value.strip(), secondary, time.perf_counter())

    def stop(self):
        self._running= False
        self.wait() #waits for thread to finish (the reading in progress ends first)
