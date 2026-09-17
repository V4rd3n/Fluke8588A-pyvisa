from PyQt6.QtCore import QThread, pyqtSignal
class ReadingThread(QThread):
    reading_ready = pyqtSignal(str)
    def __init__(self, instr_ctrl):
        super().__init__()
        self._instr_ctrl = instr_ctrl
        self._running = False
    
    def run(self):
        self._instr_ctrl.write("INIT:CONT ON")
        self._running=True
        while self._running:
            value = self._instr_ctrl.query("FETCH?")
            self.reading_ready.emit(value.strip()) #might be a number, remove strip in case

    def stop(self):
        self._instr_ctrl.write("ABORT")
        self._running= False
        self.wait() #waits for thread to finish