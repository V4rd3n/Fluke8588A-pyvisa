from Fluke8588A.controllers.reading_thread import ReadingThread
from Fluke8588A.instrument import scpi
from Fluke8588A.data import gui_values
from Fluke8588A.services import units
from Fluke8588A.services.statistics import RunningStatistics
from PyQt6.QtCore import QObject, pyqtSignal
import logging

logger = logging.getLogger(__name__)

class AcquisitionController(QObject):
	"""
	Presenter of the graph window, the only one that talks to it: owns the
	reading thread, the acquired data (base unit, time in s from the first
	reading) and their statistics, and sets the graph unit from the range.
	With a secondary reading (ACV/ACI) it is read together with the primary
	one and goes to the second graph, with its own data and statistics.

	The thread shares the instrument with the writes of AppController: stop()
	must be called before any command is sent to the instrument.
	"""
	status_changed = pyqtSignal(str)

	def __init__(self, instr_ctrl, graph_window):
		super().__init__()
		self._instr_ctrl = instr_ctrl
		self._graph_window = graph_window
		self._reading_thread = None
		self._first_reading_time = None
		self._overload = False
		self._secondary = False
		self._secondary_unavailable = False
		self._times = []
		self._values = []
		self._statistics = RunningStatistics()
		self._secondary_times = []
		self._secondary_values = []
		self._secondary_statistics = RunningStatistics()
		self._graph_window.start_requested.connect(self._on_start_requested)
		self._graph_window.stop_requested.connect(self._on_stop_requested)

	def show_function(self, function: str, secondary_reading: str | None = None) -> None:
		"""Show the graph window for a function, secondary_reading is None when OFF."""
		self._secondary = secondary_reading is not None
		self._clear()
		self._graph_window.show_function(function, secondary_reading)

	def show_range_unit(self, quantity: str, base_unit: str, settings) -> None:
		"""Graph unit from the range: mV for 100 mV, V for 1 V..., SI prefix chosen by the axis in AUTO."""
		unit = None
		if settings.range_mode == gui_values.RANGE_MODE_MAN:
			unit = units.range_unit(settings.range_val, base_unit)
		if unit is None:
			self._graph_window.set_primary_unit(quantity, base_unit)
		else:
			self._graph_window.set_primary_unit(quantity, base_unit, *unit)

	def show_secondary_unit(self, quantity: str, base_unit: str) -> None:
		"""Unit of the secondary reading, SI prefix chosen by the axis (no range to take it from)."""
		self._graph_window.set_secondary_unit(quantity, base_unit)

	def stop(self) -> None:
		"""Stop the reading thread, if any: the instrument is free again on return."""
		if self._reading_thread is None:
			return
		logger.debug(">>> AcquisitionController.stop")
		self._reading_thread.stop()
		self._reading_thread = None
		self._graph_window.set_running(False)
		logger.debug("<<< AcquisitionController.stop")

	def close(self) -> None:
		self.stop()
		self._graph_window.close()

	def _clear(self) -> None:
		self._first_reading_time = None
		self._overload = False
		self._secondary_unavailable = False
		self._times = []
		self._values = []
		self._statistics.reset()
		self._secondary_times = []
		self._secondary_values = []
		self._secondary_statistics.reset()
		self._graph_window.clear()

	def _on_start_requested(self):
		logger.debug(">>> _on_start_requested")
		if not self._instr_ctrl.is_connected():
			self.status_changed.emit("ERROR: not connected.")
			logger.debug("<<< _on_start_requested (not connected)")
			return
		if self._reading_thread is not None:
			logger.debug("<<< _on_start_requested (thread already running)")
			return
		try:
			# In continuous mode the memory holds the readings taken before Start
			self._instr_ctrl.discard_readings()
		except Exception as error:
			self.status_changed.emit(f"Acquisition start error: {error}")
			logger.debug(f"<<< _on_start_requested (error={error})")
			return
		# Time axis from the PC clock: READ? starts a new record each time, so
		# the instrument time stamps (FETCh? 5) are deltas inside it, always ~0 here
		self._clear()
		self._reading_thread = ReadingThread(self._instr_ctrl, self._secondary)
		self._reading_thread.reading_ready.connect(self._on_reading_ready)
		self._reading_thread.reading_failed.connect(self._on_reading_failed)
		self._reading_thread.start()
		self._graph_window.set_running(True)
		self.status_changed.emit("Acquisition started.")
		logger.debug("<<< _on_start_requested")

	def _on_stop_requested(self):
		self.stop()
		self.status_changed.emit("Acquisition stopped.")

	def _is_current_thread_signal(self) -> bool:
		# A reading emitted just before stop() is delivered afterwards: it
		# belongs to a stopped acquisition (the graph may be cleared already)
		return self._reading_thread is not None and self.sender() is self._reading_thread

	def _on_reading_ready(self, text: str, secondary_text: str | None, timestamp: float):
		if not self._is_current_thread_signal():
			return
		# A READ? answer holds TRIGger:COUNt readings, in continuous mode all the
		# readings taken since the previous one (comma separated): they all get
		# the arrival time of the answer
		added = False
		for item in text.split(","):
			value = float(item)
			if value >= scpi.INVALID_READING:
				continue
			# Overloads stay out of curve and statistics, the status bar tells
			# when they start and end (not at every reading)
			overload = abs(value) >= scpi.OVERLOAD_READING
			if overload != self._overload:
				self._overload = overload
				self.status_changed.emit(
					"OVERLOAD: readings out of range, not shown." if overload else "Readings back in range."
				)
			if overload:
				continue
			self._times.append(self._elapsed(timestamp))
			self._values.append(value)
			self._statistics.add(value)
			added = True
		if self._secondary:
			added = self._add_secondary(secondary_text, timestamp) or added
		# The window is redrawn once per answer, not once per reading
		if added:
			self._show_data()

	def _add_secondary(self, text: str | None, timestamp: float) -> bool:
		"""Add the secondary readings of an answer, True when at least one is valid."""
		if text is None:
			# Continuous mode: the status bar tells it once per acquisition
			if not self._secondary_unavailable:
				self._secondary_unavailable = True
				self.status_changed.emit("Secondary reading not available in continuous mode (INIT:CONT ON).")
			return False
		added = False
		# FETCh? 2 has as many readings as READ?, invalid ones (e.g. frequency
		# without signal) and overloads are left out silently: the primary
		# reading already tells about the overload
		for item in text.split(","):
			value = float(item)
			if abs(value) >= scpi.OVERLOAD_READING:
				continue
			self._secondary_times.append(self._elapsed(timestamp))
			self._secondary_values.append(value)
			self._secondary_statistics.add(value)
			added = True
		return added

	def _elapsed(self, timestamp: float) -> float:
		"""Time from the first valid reading, primary or secondary."""
		if self._first_reading_time is None:
			self._first_reading_time = timestamp
		return timestamp - self._first_reading_time

	def _show_data(self) -> None:
		statistics = self._statistics
		self._graph_window.set_primary_curve(self._times, self._values)
		self._graph_window.set_primary_statistics(
			statistics.count,
			statistics.last,
			statistics.mean,
			statistics.stdev,
			statistics.stdev_mean,
		)
		if not self._secondary:
			return
		statistics = self._secondary_statistics
		self._graph_window.set_secondary_curve(self._secondary_times, self._secondary_values)
		self._graph_window.set_secondary_statistics(
			statistics.count,
			statistics.last,
			statistics.mean,
			statistics.stdev,
			statistics.stdev_mean,
		)

	def _on_reading_failed(self, error: str):
		if not self._is_current_thread_signal():
			return
		self.stop()
		self.status_changed.emit(f"Read error: {error}")
		logger.debug(f"    READ_ERROR: {error}")
