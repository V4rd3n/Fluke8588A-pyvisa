from PyQt6.QtCore import QThread, pyqtSignal
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Interval of the status queries during the acquisition, also the longest wait of a Stop
POLL_INTERVAL_MS = 100


class DigitizeThread(QThread):
    # Readings of the block (numpy array), its time stamps (numpy array of
    # FETCh? 5, None without them) and the errors queued by the instrument, "" when none
    block_ready = pyqtSignal(object, object, str)
    block_failed = pyqtSignal(str)

    def __init__(self, instr_ctrl, count: int, continuous: bool = False, time_stamps: bool = False):
        super().__init__()
        self._instr_ctrl = instr_ctrl
        self._count = count
        # Continuous: a new block right after each one, until stop()
        self._continuous = continuous
        # Time stamps ON for the acquisition only: the setting is shared by all the functions
        self._time_stamps = time_stamps
        self._running = True

    def run(self):
        try:
            if self._time_stamps:
                self._instr_ctrl.set_time_stamps(True)
            while self._running:
                values, stamps, errors = self._acquire_block()
                if values is None:
                    return
                self.block_ready.emit(values, stamps, errors)
                if not self._continuous:
                    return
        except Exception as error:
            self.block_failed.emit(str(error))
        finally:
            if self._time_stamps:
                self._time_stamps_off()

    def _acquire_block(self):
        """Readings, time stamps and queued errors of one block, (None, None, "") when stopped meanwhile."""
        self._instr_ctrl.start_digitize()
        # Without a timeout: an external trigger may arrive at any time
        while self._running and self._instr_ctrl.is_measuring():
            self.msleep(POLL_INTERVAL_MS)
        if not self._running:
            self._instr_ctrl.abort()
            return None, None, ""
        text = self._instr_ctrl.fetch_block(self._count)
        stamps = None
        if self._time_stamps:
            stamps = np.array(self._instr_ctrl.fetch_time_stamps(self._count).strip().split(","), dtype=float)
        errors = self._queued_errors()
        return np.array(text.strip().split(","), dtype=float), stamps, errors

    def _time_stamps_off(self):
        # A failure here must not hide the result of the acquisition
        try:
            self._instr_ctrl.set_time_stamps(False)
        except Exception as error:
            logger.debug(f"    TIME_STAMPS_OFF_ERROR: {error}")

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
