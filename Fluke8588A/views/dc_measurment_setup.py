from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QWidget
import os
dc_measurment_setup_loc = os.path.join(os.path.dirname(__file__), "..", "ui", "dc_measurment_setup.ui")

class DcMeasurmentWindow(QWidget):
	mode_select=pyqtSignal(str)
	time_select=pyqtSignal(float)
	nplc_select=pyqtSignal(float)
	def __init__(self):
		super().__init__()
		self._line_frequency = None
		uic.loadUi(dc_measurment_setup_loc, self)
		self._init_widgets()
		self._connect_signals()

	def _init_widgets(self):
		self.nplc_spin.setDecimals(3)  # Allow 4 decimal places
		self.nplc_spin.setSingleStep(0.01)  # Step by 0.0001
		
		self.time_spin.setDecimals(4)
		self.time_spin.setSingleStep(0.01)
		
		self.nplc_spin.valueChanged.connect(self._update_time)
		self.time_spin.valueChanged.connect(self._update_nplc)

	def set_line_frequency(self, line_frequency: float) -> None:
		if line_frequency <= 0:
			raise ValueError("Line frequency must be greater than zero")
		self._line_frequency = line_frequency

	def set_aperture_ranges(
		self,
		min_time: float,
		max_time: float,
		min_nplc: float,
		max_nplc: float,
	) -> None:
		self.nplc_spin.setRange(min_nplc, max_nplc)
		self.time_spin.setRange(min_time, max_time)

	def _connect_signals(self):
		self.confirm_box.accepted.connect(self._on_confirm)
		self.confirm_box.rejected.connect(self._on_cancel)
	
	def _on_confirm(self):
		if self.auto_check.isChecked():
			mode = "AUTO"
		elif self.fast_check.isChecked():
			mode = "FAST"
		else:
			mode = "MAN"
		self.mode_select.emit(mode)
		self.time_select.emit(self.time_spin.value())
		self.nplc_select.emit(self.nplc_spin.value())
		self.close()

	def _on_cancel(self):
		self.close()

	def _update_time(self):
		if self._line_frequency is not None:
			self.time_spin.setValue(float(self.nplc_spin.value()) / self._line_frequency)
	
	#the machine has minimum aperture of 0.0001 seconds, but minumim nplc of 0.01, so if the user tries selecting a value inbetween 0.0002 and 0.0001, the nplc no longer correspon to the seconds
	def _update_nplc(self):
		if self._line_frequency is not None:
			self.nplc_spin.setValue(float(self.time_spin.value() * self._line_frequency))