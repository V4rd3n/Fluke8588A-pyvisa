from Fluke8588A.data import gui_values
from Fluke8588A.services import measurement_reader, units
from Fluke8588A.services.measurement_reader import LoadedDigitize
from pathlib import Path
import logging
import numpy as np

logger = logging.getLogger(__name__)

# Quantity and base unit of the primary reading of each function, as shown by AppController
_FUNCTION_UNITS = {
	"DCV": ("Voltage", "V"),
	"DCI": ("Current", "A"),
	"ACV": ("Voltage", "V"),
	"ACI": ("Current", "A"),
	"OHMS": ("Resistance", "Ω"),
}
_DIGITIZE_UNITS = {gui_values.DIGI_SIGNAL_VOLTAGE: "V", gui_values.DIGI_SIGNAL_CURRENT: "A"}


class GraphVisualizerController:
	"""
	Presenter of the graph visualizer window: each Import loads a file of the
	program (services/measurement_reader) in its graph, on its own: primary
	reading of a measurement file, block of samples or spectrum of a digitize
	file (its LCDs then show the block values in place of the statistics). In
	continuous mode the burst spinbox of the graph chooses the block shown.
	It does not use the instrument.

	The second graph also shows, unless "Ignore secondary readings" is
	checked, what comes with the file of the first one: its secondary reading
	for a measurement file, the spectrum of the block shown for a digitize
	samples file (its _freq file), without LCDs, the first graph has them.
	"""

	def __init__(self, window):
		self._window = window
		self._window.import_requested.connect(self._on_import)
		self._window.ignore_secondary_changed.connect(self._update_secondary)
		self._window.burst_changed.connect(self._on_burst_changed)
		# File imported in each graph and its content, None before the first import
		self._files = {"prim": None, "sec": None}
		# Index in the bursts of a digitize file of the one shown in each graph
		self._burst_indexes = {"prim": 0, "sec": 0}
		# The second graph shows what came with the file of the first one
		self._secondary_from_primary = False

	def show_window(self):
		self._window.show_window()

	def close(self):
		self._window.close()

	def _on_import(self, panel: str):
		path = self._window.ask_open_path()
		if path is None:
			return
		path = Path(path)
		try:
			measurement = measurement_reader.read_file(path)
		except measurement_reader.NotMeasurementFileError as error:
			self._window.show_error(f"{path.name} is not a file of the Fluke 8588A program: {error}.")
			return
		except OSError as error:
			logger.exception("Import of %s failed", path)
			self._window.show_error(f"{path.name} could not be read or updated: {error}")
			return
		if isinstance(measurement, LoadedDigitize) and not measurement.bursts:
			self._window.show_error(f"{path.name}: no blocks in the file.")
			return
		self._files[panel] = (path, measurement)
		self._burst_indexes[panel] = 0
		if panel == "sec":
			self._secondary_from_primary = False
		self._show_file(panel)
		if panel == "prim":
			self._update_secondary()
		if isinstance(measurement, LoadedDigitize):
			# Only the first graph looks for the spectrum file
			if panel == "prim" and measurement.spectrum_error is not None:
				self._window.show_information(
					f"The spectrum file of {path.name} could not be read: {measurement.spectrum_error}."
				)
		elif measurement.repaired:
			self._window.show_information(
				f"The statistics of {path.name} were missing or did not match its readings: "
				"computed from the readings and written in the file."
			)

	def _on_burst_changed(self, panel: str, number: int):
		if self._files[panel] is None or not isinstance(self._files[panel][1], LoadedDigitize):
			return
		self._burst_indexes[panel] = number - 1
		self._show_burst(panel)
		# The spectrum follows the block, a file imported in the second graph stays
		if panel == "prim" and self._secondary_from_primary:
			self._update_secondary()

	def _show_file(self, panel: str):
		path, measurement = self._files[panel]
		if isinstance(measurement, LoadedDigitize):
			self._show_digitize(panel, measurement)
		else:
			self._show_primary(panel, path, measurement)

	def _show_primary(self, panel: str, path: Path, measurement):
		"""Primary reading of a measurement file in a graph, in the unit of its range."""
		quantity, base_unit = _FUNCTION_UNITS.get(measurement.function, ("Reading", ""))
		# The Unit line, when there, is the unit the file was written with
		if measurement.units and measurement.units[0]:
			base_unit = measurement.units[0]
		unit = None
		if measurement.range_label != gui_values.RANGE_MODE_AUTO:
			unit = units.range_unit(measurement.range_label, base_unit)
		self._show_reading(
			panel, f"{measurement.function} {path.name}", quantity, base_unit, unit,
			measurement.times, measurement.values, measurement.statistics,
		)

	def _show_digitize(self, panel: str, measurement: LoadedDigitize):
		"""Graph ready for the blocks (samples or spectra) of a digitize file, the block shown in it."""
		self._prepare_digitize_graph(panel, measurement, measurement.spectrum_only)
		self._window.set_burst_count(panel, len(measurement.bursts) if measurement.continuous else 0)
		self._show_burst(panel)

	def _prepare_digitize_graph(self, panel: str, measurement: LoadedDigitize, spectrum: bool):
		quantity, base_unit = _digitize_unit(measurement)
		self._window.clear(panel)
		self._window.set_markers(panel, False)
		if spectrum:
			self._window.set_x_label(panel, "Frequency", "Hz")
			self._window.set_unit(panel, "Magnitude", f"dB{base_unit}", f"dB{base_unit}", 1.0)
		else:
			# The LCDs mix units: axis in the base unit, no SI prefix of its own
			self._window.set_unit(panel, quantity, base_unit, base_unit, 1.0)
			if measurement.sample_rate is None:
				self._window.set_x_label(panel, "Sample", None)

	def _show_burst(self, panel: str):
		"""Block shown of the digitize file of a graph, its values on the LCDs."""
		path, measurement = self._files[panel]
		burst = measurement.bursts[self._burst_indexes[panel]]
		if measurement.spectrum_only:
			self._set_spectrum(panel, path.name, burst)
			samples = measurement.samples
		else:
			title = f"DIGITIZE {path.name}"
			if burst.number is not None:
				title += f", burst {burst.number}"
			self._window.set_file_title(panel, title)
			self._window.set_curve(panel, *_finite(burst.x, burst.values))
			samples = len(burst.values)
		self._window.set_digitize_values(
			panel, _digitize_unit(measurement)[1], samples, measurement.sample_rate,
			burst.peak, burst.peak_frequency, burst.thd_dbc,
		)

	def _update_secondary(self):
		"""What comes with the file of the first graph in the second one, unless ignored."""
		if self._files["prim"] is None:
			return
		path, measurement = self._files["prim"]
		if isinstance(measurement, LoadedDigitize):
			available = measurement.spectrum_path is not None
		else:
			available = measurement.secondary_values is not None
		if not available or self._window.is_ignore_secondary():
			# Only what came from the first file goes away, a file imported there stays
			if self._secondary_from_primary:
				self._window.clear("sec")
				self._secondary_from_primary = False
			return
		# The second graph no longer shows its own file
		self._files["sec"] = None
		if isinstance(measurement, LoadedDigitize):
			burst = measurement.bursts[self._burst_indexes["prim"]]
			self._prepare_digitize_graph("sec", measurement, spectrum=True)
			self._window.set_values_visible("sec", False)
			self._set_spectrum("sec", measurement.spectrum_path.name, burst)
		else:
			self._show_secondary(path, measurement)
		self._secondary_from_primary = True
		self._window.show_second_graph()

	def _show_secondary(self, path: Path, measurement):
		secondary_reading = measurement.settings.get("secondary_reading", "")
		primary_unit = measurement.units[0] if measurement.units else ""
		quantity, base_unit = units.ac_secondary_unit(secondary_reading, primary_unit)
		if len(measurement.units) > 1:
			base_unit = measurement.units[1]
		# No range for the secondary reading: SI prefix chosen by the axis
		self._show_reading(
			"sec", f"{measurement.function} {path.name}, secondary: {secondary_reading}", quantity, base_unit,
			None, measurement.secondary_times, measurement.secondary_values, measurement.secondary_statistics,
		)

	def _set_spectrum(self, panel: str, name: str, burst):
		"""Spectrum of a block in a graph ready for it (_prepare_digitize_graph), its file name in the title."""
		title = name
		if burst.number is not None:
			title += f", burst {burst.number}"
		if burst.freqs is None:
			title += ": no spectrum in the file"
			self._window.set_curve(panel, [], [])
		else:
			if burst.window_name:
				title += f", window {burst.window_name}"
			# A bin at exactly zero is -inf dB, the curve cannot draw it
			self._window.set_curve(panel, *_finite(burst.freqs, burst.magnitude_db))
		self._window.set_file_title(panel, title)

	def _show_reading(self, panel: str, title: str, quantity: str, base_unit: str, unit: tuple[str, float] | None,
					  times: list[float], values: list[float], statistics):
		self._window.clear(panel)
		if unit is None:
			self._window.set_unit(panel, quantity, base_unit)
		else:
			self._window.set_unit(panel, quantity, base_unit, *unit)
		self._window.set_file_title(panel, title)
		self._window.set_curve(panel, times, values)
		self._window.set_statistics(
			panel,
			statistics.count,
			statistics.last,
			statistics.mean,
			statistics.stdev,
			statistics.stdev_mean,
		)


def _digitize_unit(measurement: LoadedDigitize) -> tuple[str, str]:
	"""Quantity and base unit of a digitize file, from the signal; the Unit line when there."""
	signal = measurement.settings.get("signal", "")
	base_unit = measurement.unit or _DIGITIZE_UNITS.get(signal, "")
	return (signal or "Signal"), base_unit


def _finite(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
	"""Points with a finite value only: overloads (nan) and -inf dB left out."""
	keep = np.isfinite(y)
	return x[keep], y[keep]
