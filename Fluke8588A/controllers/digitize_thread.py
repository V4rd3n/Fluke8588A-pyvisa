from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np

# Interval of the status queries during the acquisition, also the longest wait of a Stop
POLL_INTERVAL_MS = 100


class DigitizeThread(QThread):
    # Readings of the block (numpy array) and the errors queued by the instrument, "" when none
    block_ready = pyqtSignal(object, str)
    block_failed = pyqtSignal(str)

    def __init__(self, instr_ctrl, count: int, continuous: bool = False):
        super().__init__()
        self._instr_ctrl = instr_ctrl
        self._count = count
        # Continuous: a new block right after each one, until stop()
        self._continuous = continuous
        self._running = True

    def run(self):
        while self._running:
            try:
                values, errors = self._acquire_block()
            except Exception as error:
                self.block_failed.emit(str(error))
                return
            if values is None:
                return
            self.block_ready.emit(values, errors)
            if not self._continuous:
                return

    def _acquire_block(self):
        """Readings and queued errors of one block, (None, "") when stopped meanwhile."""
        self._instr_ctrl.start_digitize()
        # Without a timeout: an external trigger may arrive at any time
        while self._running and self._instr_ctrl.is_measuring():
            self.msleep(POLL_INTERVAL_MS)
        if not self._running:
            self._instr_ctrl.abort()
            return None, ""
        text = self._instr_ctrl.fetch_block(self._count)
        errors = self._queued_errors()
        return np.array(text.strip().split(","), dtype=float), errors

    def _queued_errors(self) -> str:
        # An error does not throw the block away: the controller shows both
        try:
            self._instr_ctrl.check_errors()
        except RuntimeError as error:
            return str(error)
        return ""

    def stop(self):
        self._running = False
        self.wait()  # an abort or a block transfer in progress ends first
