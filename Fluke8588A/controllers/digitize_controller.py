from Fluke8588A.controllers.digitize_thread import DigitizeThread
from Fluke8588A.data import gui_values
from Fluke8588A.instrument import scpi
from Fluke8588A.services import fft
from Fluke8588A.services import measurement_file
from Fluke8588A.views import plot_export
from PyQt6.QtCore import QObject, pyqtSignal
from datetime import datetime
from pathlib import Path
import logging
import numpy as np

logger = logging.getLogger(__name__)

class DigitizeController(QObject):
	"""
	Presenter of the digitize window, the only one that talks to it: owns the
	acquisition thread, the block acquired and its FFT. A digitize acquisition
	is a single block of samples, so it does not share AcquisitionController,
	which reads continuously into the graph window. In continuous mode the
	blocks follow one another until Stop, each one replacing the previous in
	the window. Averaged, in continuous mode only, the window shows the
	average of the bursts sample by sample and the FFT of the average.

	With Base FFT Settings the trigger is set from samples and sample rate,
	otherwise it stays as set in the trigger windows. The trigger state belongs
	to AppController: apply_trigger(samples, rate) sets it and read_trigger()
	reads it, both return it in GUI format.

	The samples are saved in the temp folder (services/measurement_file) as
	the blocks arrive, the spectra in a second file: in continuous mode all of
	them, each after a '# burst N' line ('# burst N window X' for the
	spectra). At the end of the acquisition the graphs of the block shown and
	of its spectrum are saved too; Save copies files and graphs where the
	user chooses, the spectrum as <name>_freq. Averaged, the spectra of the
	bursts are not computed: at the end the average and its spectrum go in
	<name>_avg and <name>_freq_avg, next to the file of all the bursts.

	The thread shares the instrument with the writes of AppController: stop()
	must be called before any command is sent to the instrument.
	"""
	status_changed = pyqtSignal(str)

	def __init__(self, instr_ctrl, digitize_window, apply_trigger, read_trigger):
		super().__init__()
		self._instr_ctrl = instr_ctrl
		self._digitize_window = digitize_window
		self._apply_trigger = apply_trigger
		self._read_trigger = read_trigger
		self._thread = None
		self._settings = None
		self._quantity = ""
		self._unit = ""
		self._values = None
		# Date and time of the Start, in the file names and headers
		self._start_datetime = None
		# None when the trigger does not give a known sample rate
		self._rate = None
		self._requested_count = 0
		self._continuous = False
		self._averaged = False
		self._burst_count = 0
		# Last block received; _values is the block shown, the average when averaged
		self._block = None
		# Sum and number of the samples in range at each index, over the bursts averaged
		self._sum = None
		self._valid = None
		self._averaged_count = 0
		self._results = None
		# Temp files of the samples and of the spectrum, None when not written;
		# averaged, the spectrum is the one of the average
		self._time_path = None
		self._fft_path = None
		self._avg_time_path = None
		# A file misses blocks after an error: Save writes the block shown instead
		self._time_file_failed = False
		self._fft_file_failed = False
		self._save_directory = None
		self._digitize_window.start_requested.connect(self._on_start_requested)
		self._digitize_window.stop_requested.connect(self._on_stop_requested)
		self._digitize_window.save_requested.connect(self._on_save_requested)
		self._digitize_window.fft_window_changed.connect(self._on_fft_window_changed)

	def show_function(self, settings) -> None:
		"""Show the digitize window, settings (GUI format) are those applied."""
		self._settings = settings
		self._clear()
		if settings.signal == gui_values.DIGI_SIGNAL_VOLTAGE:
			self._quantity, self._unit = "Voltage", "V"
		else:
			self._quantity, self._unit = "Current", "A"
		self._digitize_window.show_signal(self._quantity, self._unit)

	def stop(self) -> None:
		"""Stop the acquisition, if any: the instrument is free again on return."""
		if self._thread is None:
			return
		logger.debug(">>> DigitizeController.stop")
		self._thread.stop()
		self._thread = None
		self._digitize_window.set_running(False)
		logger.debug("<<< DigitizeController.stop")

	def hide_window(self) -> None:
		"""Hide the digitize window, for a function that does not use it."""
		self.stop()
		self._digitize_window.hide()

	def close(self) -> None:
		self.stop()
		self._digitize_window.close()

	def _clear(self) -> None:
		self._values = None
		self._rate = None
		self._results = None
		self._time_path = None
		self._fft_path = None
		self._avg_time_path = None
		self._time_file_failed = False
		self._fft_file_failed = False
		self._burst_count = 0
		self._block = None
		self._sum = None
		self._valid = None
		self._averaged_count = 0
		self._digitize_window.clear()
		self._digitize_window.set_save_enabled(False)

	def _on_start_requested(self):
		logger.debug(">>> DigitizeController._on_start_requested")
		if not self._instr_ctrl.is_connected():
			self.status_changed.emit("ERROR: not connected.")
			return
		if self._thread is not None:
			return
		try:
			count, rate = self._prepare_trigger()
		except Exception as error:
			self.status_changed.emit(f"DIGITIZE start error: {error}")
			logger.debug(f"<<< DigitizeController._on_start_requested (error={error})")
			return
		self._clear()
		self._start_datetime = datetime.now()
		self._rate = rate
		self._requested_count = count
		self._continuous = self._digitize_window.is_continuous()
		self._averaged = self._continuous and self._digitize_window.is_averaged()
		self._thread = DigitizeThread(self._instr_ctrl, count, self._continuous)
		self._thread.block_ready.connect(self._on_block_ready)
		self._thread.block_failed.connect(self._on_block_failed)
		self._thread.start()
		self._digitize_window.set_running(True)
		mode = ""
		if self._continuous:
			mode = " in continuous mode, averaged" if self._averaged else " in continuous mode"
		self.status_changed.emit(f"Digitizing {count} samples{mode}...")
		logger.debug(
			f"<<< DigitizeController._on_start_requested (count={count}, rate={rate}, "
			f"continuous={self._continuous}, averaged={self._averaged})"
		)

	def _prepare_trigger(self) -> tuple[int, float | None]:
		"""Trigger ready for the acquisition, returns samples expected and sample rate (None when unknown)."""
		if not self._digitize_window.is_base_fft():
			trigger = self._read_trigger()
			count = trigger.arm2.count * trigger.arm1.count * trigger.trigger.count
			return count, self._trigger_rate(trigger)
		count = self._digitize_window.samples()
		rate = self._digitize_window.sample_rate()
		# A shorter period gives "trigger too fast" and fewer samples than requested
		min_period = self._settings.aperture + scpi.DIGI_READING_TIME
		if 1 / rate < min_period * (1 - 1e-9):
			raise ValueError(
				f"sample rate too high for aperture {self._settings.aperture:g} s: "
				f"at most {1 / min_period:g} Hz"
			)
		trigger = self._apply_trigger(count, rate)
		# The instrument may round the timer: the FFT needs the rate it really uses
		rate = 1 / trigger.timer
		self._digitize_window.set_sample_rate(rate)
		return trigger.count, rate

	@staticmethod
	def _trigger_rate(trigger) -> float | None:
		"""Sample rate of a trigger state, None when the samples are not evenly spaced at a known rate."""
		layer = trigger.trigger
		if (
			layer.source != gui_values.TRIGGER_SOURCE_TIMER
			or layer.ecount != 1
			or trigger.arm1.count != 1
			or trigger.arm2.count != 1
			# Longer than the timer, they make the rate slower than 1/timer (operator manual)
			or layer.delay + layer.holdoff >= layer.timer
		):
			return None
		return 1 / layer.timer

	def _on_block_ready(self, values, errors: str):
		if self.sender() is not self._thread or self._thread is None:
			return
		if not self._continuous:
			self.stop()
		self._burst_count += 1
		self._digitize_window.set_burst_count(self._burst_count)
		# Overloads and invalid readings are left out of curve, average and FFT
		bad = np.abs(values) >= scpi.OVERLOAD_READING
		values[bad] = np.nan
		self._block = values
		messages = [f"{len(values)} samples acquired."]
		if self._continuous:
			messages.insert(0, f"Burst {self._burst_count}:")
		if len(values) != self._requested_count:
			messages.append(f"WARNING: {self._requested_count} requested, trigger too fast?")
		if self._averaged:
			messages.append(self._add_to_average(values))
		else:
			self._values = values
		self._digitize_window.set_time_curve(self._values, self._rate)
		# While running the block changes at every burst: saved after Stop
		self._digitize_window.set_save_enabled(self._thread is None)
		if bad.any():
			left_out = "left out of the average" if self._averaged else "no FFT"
			messages.append(f"OVERLOAD: {np.count_nonzero(bad)} samples out of range, {left_out}.")
		out_of_range = np.isnan(self._values).any()
		if self._averaged and out_of_range:
			messages.append("Samples never in range in the average: no FFT.")
		elif not out_of_range and self._rate is None:
			messages.append("Sample rate unknown from the trigger: time graph only, no FFT.")
		if errors:
			messages.append(errors)
		fft_message = self._update_fft()
		if fft_message:
			messages.append(fft_message)
		temp_message = self._append_temp()
		# In continuous mode the last block is known only at Stop
		if self._thread is None:
			temp_message = self._finish_temp() or temp_message
		if temp_message:
			messages.append(temp_message)
		self.status_changed.emit(" ".join(messages))

	def _on_block_failed(self, error: str):
		if self.sender() is not self._thread or self._thread is None:
			return
		self.stop()
		self.status_changed.emit(f"DIGITIZE error: {error}")
		logger.debug(f"    DIGITIZE_ERROR: {error}")

	def _on_stop_requested(self):
		self.stop()
		if self._continuous and self._values is not None:
			# The burst in progress is discarded, the last one completed stays
			self._digitize_window.set_save_enabled(True)
			shown = f"average of {self._averaged_count} shown" if self._averaged else "last one shown"
			message = f"Digitize stopped after {self._burst_count} bursts, {shown}."
			temp_message = self._finish_temp()
			self.status_changed.emit(f"{message} {temp_message}" if temp_message else message)
		else:
			self.status_changed.emit("Digitize stopped, samples discarded.")

	def _on_fft_window_changed(self):
		# The block is already there: no need of a new acquisition
		if self._thread is None and self._values is not None:
			message = self._update_fft()
			if self._continuous and not self._averaged:
				# The file has the spectrum of every burst, each with the window of its time
				message = message or "Spectrum file unchanged: it keeps the window of each burst."
			elif self._shown_time_path() is not None:
				# The spectrum saved is the one of the window shown
				message = self._save_fft_temp() or message
			if message:
				self.status_changed.emit(message)

	def _update_fft(self) -> str | None:
		"""FFT of the block with the window selected, returns a message when it cannot be computed."""
		self._results = None
		self._digitize_window.clear_fft()
		if self._rate is None or np.isnan(self._values).any():
			return None
		window_name = self._digitize_window.fft_window()
		freqs = fft.frequencies(len(self._values), self._rate)
		try:
			magnitude, peak, peak_frequency, thd = fft.calculate_fft(self._values, freqs, window_name)
		except ValueError as error:
			# No local maximum in the spectrum: too few samples or a flat block
			logger.debug(f"    FFT_ERROR: {error}")
			return "FFT not available: no peak in the spectrum."
		self._results = fft.FftResults(window_name, freqs, magnitude, peak, peak_frequency, thd)
		self._digitize_window.set_frequency_curve(freqs, magnitude)
		self._digitize_window.set_results(peak, peak_frequency, thd)
		return None

	def _add_to_average(self, values) -> str:
		"""Burst just arrived into the average shown, each sample over the bursts it was in range; returns a message."""
		if self._sum is None:
			self._sum = np.zeros(len(values))
			self._valid = np.zeros(len(values), dtype=int)
		elif len(values) != len(self._sum):
			return f"Not averaged: {len(values)} samples, the average has {len(self._sum)}."
		in_range = ~np.isnan(values)
		self._sum[in_range] += values[in_range]
		self._valid += in_range
		self._averaged_count += 1
		# nan where no burst was in range
		with np.errstate(invalid="ignore"):
			self._values = self._sum / self._valid
		return f"Average of {self._averaged_count} bursts."

	def _append_temp(self) -> str | None:
		"""Block just arrived at the end of the samples file in the temp folder, returns a message on error."""
		if self._time_file_failed:
			return None
		try:
			if self._time_path is None:
				measurement_file.clean_temp()
				path = measurement_file.new_temp_path(
					self._start_datetime, measurement_file.digitize_time_label(self._settings)
				)
				self._time_path = measurement_file.write_digitize_header(
					path, self._start_datetime, self._settings, self._unit, len(self._block), self._rate,
					self._continuous,
				)
				logger.debug(f"    FILE: {self._time_path}")
			# Averaged too: every burst, the average goes in its own file at the end
			burst = self._burst_count if self._continuous else None
			measurement_file.append_digitize_block(self._time_path, self._block, self._rate, burst)
		except Exception as error:
			self._time_file_failed = True
			logger.debug(f"    FILE_ERROR: {error}")
			return f"File error, samples no longer saved in temp: {error}"
		return self._append_fft_temp() if self._continuous and not self._averaged else None

	def _append_fft_temp(self) -> str | None:
		"""Continuous mode: spectrum of the burst just arrived at the end of the spectrum file, a message on error."""
		if self._results is None or self._time_path is None or self._fft_file_failed:
			return None
		try:
			if self._fft_path is None:
				path = measurement_file.digitize_frequency_name(self._time_path)
				self._fft_path = measurement_file.write_digitize_fft(
					path, self._start_datetime, self._settings, self._unit, len(self._values), self._rate,
					continuous=True,
				)
				logger.debug(f"    FILE: {self._fft_path}")
			measurement_file.append_digitize_spectrum(self._fft_path, self._results, self._burst_count)
		except Exception as error:
			self._fft_file_failed = True
			logger.debug(f"    FILE_ERROR: {error}")
			return f"File error, spectra no longer saved in temp: {error}"
		return None

	def _finish_temp(self) -> str | None:
		"""End of the acquisition: graphs of the block shown and of its spectrum in the temp folder, a message on error."""
		try:
			if self._time_path is not None:
				# Averaged, the graph of the bursts file is of the last burst
				self._export_time_png(measurement_file.png_path(self._time_path), self._block)
			if self._continuous and not self._averaged:
				# The spectra are already in the file, the graph is of the last one
				if self._fft_path is not None and self._results is not None:
					self._export_fft_png(measurement_file.png_path(self._fft_path))
				return None
		except Exception as error:
			logger.debug(f"    PNG_ERROR: {error}")
			return f"Graph PNG error: {error}"
		if self._averaged and self._time_path is not None:
			try:
				self._avg_time_path = self._write_time(measurement_file.digitize_average_name(self._time_path))
			except Exception as error:
				logger.debug(f"    FILE_ERROR: {error}")
				return f"File error, average not saved in temp: {error}"
			logger.debug(f"    FILE: {self._avg_time_path}")
		return self._save_fft_temp()

	def _shown_time_path(self) -> Path | None:
		"""Temp file of the block shown: the average when averaged."""
		return self._avg_time_path if self._averaged else self._time_path

	def _save_fft_temp(self) -> str | None:
		"""
		Single block or average: spectrum shown in the temp folder with its
		graph, the same file at every window change.
		"""
		time_path = self._shown_time_path()
		if time_path is None:
			return None
		try:
			if self._results is None:
				# No spectrum with the window shown: the one of the previous window is no longer valid
				if self._fft_path is not None:
					self._fft_path.unlink(missing_ok=True)
					measurement_file.png_path(self._fft_path).unlink(missing_ok=True)
					self._fft_path = None
				return None
			path = measurement_file.digitize_frequency_name(time_path)
			self._write_fft(path)
			self._fft_path = path
		except Exception as error:
			logger.debug(f"    FILE_ERROR: {error}")
			return f"File error, spectrum not saved in temp: {error}"
		logger.debug(f"    FILE: {self._fft_path}")
		return None

	def _burst(self) -> int | None:
		"""Number of the block shown in continuous mode, None otherwise and for the average."""
		return self._burst_count if self._continuous and not self._averaged else None

	def _averaged_bursts(self) -> int | None:
		"""Bursts in the average shown, None when not averaged."""
		return self._averaged_count if self._averaged else None

	def _write_time(self, path: Path) -> Path:
		"""CSV file and PNG graph of the block shown."""
		path = measurement_file.write_digitize_time(
			path, self._start_datetime, self._settings, self._unit, self._values, self._rate,
			self._continuous, self._burst(), self._averaged_bursts(),
		)
		self._export_time_png(measurement_file.png_path(path), self._values)
		return path

	def _export_time_png(self, path: Path, values) -> None:
		x_label, x_units = ("Sample", None) if self._rate is None else ("Time", "s")
		x = np.arange(len(values)) if self._rate is None else np.arange(len(values)) / self._rate
		plot_export.export_png(path, [
			plot_export.PlotData(x, values, x_label, x_units, self._quantity, self._unit)
		])

	def _write_fft(self, path: Path) -> Path:
		"""CSV file and PNG graph of the spectrum shown."""
		path = measurement_file.write_digitize_fft(
			path, self._start_datetime, self._settings, self._unit, len(self._values), self._rate, self._results,
			self._continuous, self._averaged_bursts(),
		)
		self._export_fft_png(measurement_file.png_path(path))
		return path

	def _export_fft_png(self, path: Path) -> None:
		plot_export.export_png(path, [
			plot_export.PlotData(
				self._results.freqs, self._results.magnitude_db, "Frequency", "Hz", f"Magnitude (dB{self._unit})", None
			)
		])

	def _on_save_requested(self):
		"""
		Samples and spectrum where the user chooses, with their graphs: copies
		of the temp files; after a temp folder error only the block shown,
		written again. Averaged, also the average as <name>_avg and its
		spectrum as <name>_freq_avg; the bursts are lost after an error of
		their temp file.
		"""
		if self._thread is not None or self._values is None:
			return
		name = (
			measurement_file.saved_name(self._time_path) if self._time_path is not None
			else f"digitize_{measurement_file.DIGITIZE_TIME_LABEL}.csv"
		)
		path = self._digitize_window.ask_save_path(name, self._save_directory)
		if path is None:
			return
		destination = Path(path)
		if not destination.suffix:
			destination = destination.with_suffix(".csv")
		avg_destination = measurement_file.digitize_average_name(destination)
		shown_destination = avg_destination if self._averaged else destination
		fft_destination = measurement_file.digitize_frequency_name(shown_destination)
		saved = []
		try:
			if self._time_path is not None and not self._time_file_failed:
				measurement_file.save_copy(self._time_path, destination)
				saved.append(destination)
			elif not self._averaged:
				self._write_time(destination)
				saved.append(destination)
			if self._averaged:
				if self._avg_time_path is not None:
					measurement_file.save_copy(self._avg_time_path, avg_destination)
				else:
					self._write_time(avg_destination)
				saved.append(avg_destination)
			if self._fft_path is not None and not self._fft_file_failed:
				measurement_file.save_copy(self._fft_path, fft_destination)
				saved.append(fft_destination)
			elif self._results is not None:
				self._write_fft(fft_destination)
				saved.append(fft_destination)
		except Exception as error:
			self.status_changed.emit(f"Save error: {error}")
			logger.debug(f"    SAVE_ERROR: {error}")
			return
		self._save_directory = str(destination.parent)
		names = str(saved[0])
		if len(saved) > 1:
			names += " and " + ", ".join(path.name for path in saved[1:])
		self.status_changed.emit(f"Saved {names}, with the graphs")
