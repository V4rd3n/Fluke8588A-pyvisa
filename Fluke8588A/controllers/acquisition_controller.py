from Fluke8588A.controllers.allan_thread import AllanThread
from Fluke8588A.controllers.reading_thread import ReadingThread
from Fluke8588A.instrument import scpi
from Fluke8588A.data import gui_values
from Fluke8588A.services import units
from Fluke8588A.services import allan
from Fluke8588A.services import measurement_file
from Fluke8588A.services.measurement_file import MeasurementFile
from Fluke8588A.services.statistics import RunningStatistics
from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime, timedelta
from pathlib import Path
import logging
import time

logger = logging.getLogger(__name__)

class AcquisitionController(QObject):
	"""
	Presenter of the graph window, the only one that talks to it: owns the
	reading thread, the acquired data (base unit, time in s from the first
	reading) and their statistics, and sets the graph unit from the range.
	With a secondary reading (ACV/ACI) it is read together with the primary
	one and goes to the second graph, with its own data and statistics.
	Every acquisition is also saved to a CSV file (services/measurement_file),
	closed with the final statistics when the acquisition stops; Save copies
	the file of the acquisition shown, once stopped, where the user chooses,
	and Generate computes from it the Allan deviation of the primary reading
	(during the acquisition from the readings acquired so far), in an
	AllanThread: the window and the acquisition go on meanwhile.

	The thread shares the instrument with the writes of AppController: stop()
	must be called before any command is sent to the instrument.
	"""
	status_changed = pyqtSignal(str)

	def __init__(self, instr_ctrl, graph_window):
		super().__init__()
		self._instr_ctrl = instr_ctrl
		self._graph_window = graph_window
		self._reading_thread = None
		self._allan_thread = None
		# The AllanThread running computes data no longer shown: its result is discarded
		self._allan_discarded = False
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
		self._function = None
		self._settings = None
		self._secondary_reading = None
		self._unit = ""
		self._secondary_unit = ""
		self._file = None
		# File of the acquisition shown, for Save; folder of the last Save
		self._shown_file_path = None
		self._save_directory = None
		self._start_datetime = None
		self._start_perf_counter = None
		self._graph_window.start_requested.connect(self._on_start_requested)
		self._graph_window.stop_requested.connect(self._on_stop_requested)
		self._graph_window.save_requested.connect(self._on_save_requested)
		self._graph_window.allan_requested.connect(self._on_allan_requested)

	def show_function(self, function: str, settings, secondary_reading: str | None = None) -> None:
		"""
		Show the graph window for a function, secondary_reading is None when OFF.
		settings (GUI format) are those applied, written in the file header.
		"""
		self._secondary = secondary_reading is not None
		self._function = function
		self._settings = settings
		self._secondary_reading = secondary_reading
		self._unit = ""
		self._secondary_unit = ""
		self._clear()
		self._graph_window.show_function(function, secondary_reading)

	def show_range_unit(self, quantity: str, base_unit: str, settings) -> None:
		"""Graph unit from the range: mV for 100 mV, V for 1 V..., SI prefix chosen by the axis in AUTO."""
		self._unit = base_unit
		unit = None
		if settings.range_mode == gui_values.RANGE_MODE_MAN:
			unit = units.range_unit(settings.range_val, base_unit)
		if unit is None:
			self._graph_window.set_primary_unit(quantity, base_unit)
		else:
			self._graph_window.set_primary_unit(quantity, base_unit, *unit)

	def show_secondary_unit(self, quantity: str, base_unit: str) -> None:
		"""Unit of the secondary reading, SI prefix chosen by the axis (no range to take it from)."""
		self._secondary_unit = base_unit
		self._graph_window.set_secondary_unit(quantity, base_unit)

	def stop(self) -> None:
		"""Stop the reading thread, if any: the instrument is free again on return."""
		if self._reading_thread is None:
			return
		logger.debug(">>> AcquisitionController.stop")
		self._reading_thread.stop()
		self._reading_thread = None
		self._graph_window.set_running(False)
		self._close_file()
		self._graph_window.set_save_enabled(self._shown_file_path is not None)
		self._update_allan_enabled()
		logger.debug("<<< AcquisitionController.stop")

	def close(self) -> None:
		self.stop()
		# The thread must not be destroyed while running: its allantools call
		# cannot be interrupted, wait for it
		if self._allan_thread is not None:
			self._allan_thread.wait()
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
		# The file belongs to the data cleared from the graph
		self._shown_file_path = None
		self._graph_window.set_save_enabled(False)
		# The Allan deviation in progress is of the data cleared
		if self._allan_thread is not None:
			self._allan_discarded = True
		self._update_allan_enabled()
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
		self._open_file()
		self._reading_thread = ReadingThread(self._instr_ctrl, self._secondary)
		self._reading_thread.reading_ready.connect(self._on_reading_ready)
		self._reading_thread.reading_failed.connect(self._on_reading_failed)
		self._reading_thread.start()
		self._graph_window.set_running(True)
		self._update_allan_enabled()
		self.status_changed.emit("Acquisition started.")
		logger.debug("<<< _on_start_requested")

	def _on_stop_requested(self):
		self.stop()
		self.status_changed.emit("Acquisition stopped.")

	def _on_save_requested(self):
		"""Copy of the file of the acquisition shown, name and folder chosen in a dialog."""
		if self._reading_thread is not None or self._shown_file_path is None:
			return
		path = self._graph_window.ask_save_path(
			measurement_file.saved_name(self._shown_file_path), self._save_directory
		)
		if path is None:
			return
		try:
			saved_path = measurement_file.save_copy(self._shown_file_path, Path(path))
		except Exception as error:
			self.status_changed.emit(f"Save error: {error}")
			logger.debug(f"    SAVE_ERROR: {error}")
			return
		self._save_directory = str(saved_path.parent)
		self.status_changed.emit(f"Saved {saved_path}")

	def _on_allan_requested(self):
		"""
		Allan deviation of the primary reading, in an AllanThread: during the
		acquisition of the readings acquired so far (also without a file),
		once stopped from the file of the acquisition shown.
		"""
		if self._allan_thread is not None:
			return
		if self._reading_thread is not None:
			# Copy: the acquisition goes on adding readings (overloads left out, as in the file)
			times, values = list(self._times), list(self._values)
			load = lambda: (times, values)
			self.status_changed.emit(f"Computing the Allan deviation of {len(values)} readings acquired so far...")
		elif self._shown_file_path is not None:
			path = self._shown_file_path
			load = lambda: measurement_file.read_primary(path)
			self.status_changed.emit("Computing the Allan deviation...")
		else:
			return
		self._allan_thread = AllanThread(load)
		self._allan_thread.allan_ready.connect(self._on_allan_ready)
		self._allan_thread.allan_failed.connect(self._on_allan_failed)
		self._allan_thread.start()
		self._update_allan_enabled()

	def _on_allan_ready(self, taus, adevs, count: int):
		if not self._release_allan_thread():
			return
		if len(taus) == 0:
			self.status_changed.emit(f"Allan deviation needs at least {allan.MIN_READINGS} readings.")
			return
		self._graph_window.set_allan_curve(taus, adevs, self._unit)
		self.status_changed.emit(f"Allan deviation of {count} readings.")

	def _on_allan_failed(self, error: str):
		if not self._release_allan_thread():
			return
		self.status_changed.emit(f"Allan error: {error}")
		logger.debug(f"    ALLAN_ERROR: {error}")

	def _release_allan_thread(self) -> bool:
		"""Forget the AllanThread that emitted, False when its result is to be discarded."""
		if self._allan_thread is None or self.sender() is not self._allan_thread:
			return False
		# The signal comes at the end of run(): wait() returns at once, the
		# thread must not be destroyed while still running
		self._allan_thread.wait()
		self._allan_thread = None
		discarded, self._allan_discarded = self._allan_discarded, False
		self._update_allan_enabled()
		return not discarded

	def _update_allan_enabled(self) -> None:
		# Generate needs readings (acquisition running or its file) and no
		# computation in progress, also of data no longer shown
		has_data = self._reading_thread is not None or self._shown_file_path is not None
		self._graph_window.set_allan_enabled(has_data and self._allan_thread is None)

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
		file_values = []
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
			file_values.append("" if overload else item)
			if overload:
				continue
			self._times.append(self._elapsed(timestamp))
			self._values.append(value)
			self._statistics.add(value)
			added = True
		if self._secondary:
			added = self._add_secondary(secondary_text, timestamp) or added
		self._write_file(file_values, secondary_text, timestamp)
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

	def _open_file(self) -> None:
		"""New file for the acquisition starting: without it the acquisition goes on, graph only."""
		units = (self._unit, self._secondary_unit) if self._secondary else (self._unit,)
		try:
			self._file = MeasurementFile(self._function, self._settings, units, self._secondary_reading)
		except Exception as error:
			self._file = None
			self.status_changed.emit(f"File error, readings not saved: {error}")
			logger.debug(f"    FILE_ERROR: {error}")
			return
		# The reading times are time.perf_counter values, the file wants the date
		self._shown_file_path = self._file.path
		self._start_datetime = datetime.now()
		self._start_perf_counter = time.perf_counter()
		logger.debug(f"    FILE: {self._file.path}")

	def _write_file(self, values: list[str], secondary_text: str | None, timestamp: float) -> None:
		"""Rows of one answer: primary readings as read ('' for overloads), secondary paired by position."""
		if self._file is None or not values:
			return
		secondary_values = None
		if secondary_text is not None:
			# Invalid secondary readings (e.g. frequency without signal) stay empty
			secondary_values = [
				"" if abs(float(item)) >= scpi.OVERLOAD_READING else item for item in secondary_text.split(",")
			]
		reading_datetime = self._start_datetime + timedelta(seconds=timestamp - self._start_perf_counter)
		try:
			self._file.add_rows(reading_datetime, self._elapsed(timestamp), values, secondary_values)
		except Exception as error:
			self._file = None
			self.status_changed.emit(f"File error, readings no longer saved: {error}")
			logger.debug(f"    FILE_ERROR: {error}")

	def _close_file(self) -> None:
		"""Final statistics in the header of the file of the acquisition stopped."""
		if self._file is None:
			return
		file, self._file = self._file, None
		try:
			file.close(self._statistics, self._secondary_statistics if self._secondary else None)
		except Exception as error:
			self.status_changed.emit(f"File error: {error}")
			logger.debug(f"    FILE_ERROR: {error}")

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
