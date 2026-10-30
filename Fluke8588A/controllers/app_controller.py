from Fluke8588A.controllers.instrument_controller import InstrumentController as InstrumentController 
from Fluke8588A.instrument import scpi
from Fluke8588A.data import defaults, gui_values
from Fluke8588A.views.main_window import MainWindow  
from Fluke8588A.views.trigger_base import TriggerBaseWindow
from Fluke8588A.views.trigger_advanced import TriggerAdvancedWindow
from Fluke8588A.views.graph_window import GraphWindow
from Fluke8588A.data.settings import (
	AciSettings,
	AcvSettings,
	DciSettings,
	DcvSettings,
	DigitizeSettings,
	OhmsSettings,
	TriggerAdvancedSettings,
	TriggerBaseSettings,
	TriggerLayerSettings,
	TriggerSignalSettings,
)
from Fluke8588A.controllers.acquisition_controller import AcquisitionController
from Fluke8588A.services.translator import Translator
from Fluke8588A.services import translation_tables as tables
from Fluke8588A.services import units
from PyQt6.QtWidgets import QApplication
from dataclasses import replace
import logging

logger = logging.getLogger(__name__)

class AppController:
	TEST_MODE = True  # Set to False to disable debug output (logger level, see main.py)
	
	def __init__(self):
		self._view = MainWindow()
		self._trigger_base_pop_up = TriggerBaseWindow()
		self._trigger_advanced_pop_up = TriggerAdvancedWindow()
		self._graph_window = GraphWindow()
		# self._trigger_pop_up = TriggerWindow()
		# self._view.set_disconnected()
		# The instrument is reset on connection, so the GUI starts from the defaults
		self._dcv_settings = defaults.dcv_settings()
		self._dci_settings = defaults.dci_settings()
		self._acv_settings = defaults.acv_settings()
		self._aci_settings = defaults.aci_settings()
		self._ohms_settings = defaults.ohms_settings()
		self._digitize_settings = defaults.digitize_settings()
		self._trigger_base_settings = defaults.trigger_base_settings()
		self._trigger_base_pop_up.set_settings(self._trigger_base_settings)
		self._trigger_advanced_settings = defaults.trigger_advanced_settings()
		self._trigger_advanced_pop_up.set_settings(self._trigger_advanced_settings)
		
		self._connect_signals()
		QApplication.instance().aboutToQuit.connect(
			self._on_application_about_to_quit
		)
		self._view.show()
		self._instr_ctrl=InstrumentController()
		self._acquisition = AcquisitionController(self._instr_ctrl, self._graph_window)
		self._acquisition.status_changed.connect(self._view.set_status)
		self._line_frequency = None
		self._reading_thread= None
		self._translator = Translator()
		self._pre_translate_defaults()

	def _pre_translate_defaults(self):
		"""Translate default GUI settings to machine format upon initialization."""
		logger.debug(">>> _pre_translate_defaults")
		self._view.set_dcv_settings(self._dcv_settings)
		self._view.set_dci_settings(self._dci_settings)
		self._view.set_acv_settings(self._acv_settings)
		self._view.set_aci_settings(self._aci_settings)
		self._view.set_ohms_settings(self._ohms_settings)
		self._view.set_digitize_settings(self._digitize_settings)
		self._update_view_aperture_values()
		logger.debug("<<< _pre_translate_defaults")

	def _connect_signals(self):
		self._view.scan_requested.connect(self._on_scan)
		self._view.connect_requested.connect(self._on_connect)
		self._view.disconnect_requested.connect(self._on_disconnect)
		self._view.dcv_set_requested.connect(self._on_dcv_set)
		self._view.dci_set_requested.connect(self._on_dci_set)
		self._view.acv_set_requested.connect(self._on_acv_set)
		self._view.aci_set_requested.connect(self._on_aci_set)
		self._view.ohms_set_requested.connect(self._on_ohms_set)
		self._view.digitize_set_requested.connect(self._on_digitize_set)
		self._view.trigger_base_requested.connect(self._on_trigger_base_press)
		self._trigger_base_pop_up.set_requested.connect(self._on_trigger_base_set)
		self._trigger_base_pop_up.reset_requested.connect(self._on_trigger_base_reset)
		self._view.trigger_advanced_requested.connect(self._on_trigger_advanced_press)
		self._trigger_advanced_pop_up.set_requested.connect(self._on_trigger_advanced_set)
		self._trigger_advanced_pop_up.reset_requested.connect(self._on_trigger_advanced_reset)
		self._view.aperture_value_changed.connect(self._on_aperture_value_changed)
		self._view.closed.connect(self._on_main_window_closed)
		""" self._view.init_requested.connect(self._on_init)
		self._view.mode_changed.connect(self._on_mode_change)
		self._view.read_requested.connect(self._on_read)
		self._view.set_requested.connect(self._on_set)
		self._view.dcv_signal.connect(self._on_dcv_setting_change)
		self._view.dci_signal.connect(self._on_dci_setting_change)
		self._view.ohms_signal.connect(self._on_ohms_setting_change)
		self._view.continuous_start_requested.connect(self._on_continuous_start)
		self._view.continuous_stop_requested.connect(self._on_continuous_stop) """

	'''
	Unused: not connected to any signal, the new view has no read display
	(set_read) yet.
	def _on_read(self):
		logger.debug(f">>> _on_read")
		if not self._instr_ctrl.is_connected():
			self._view.set_status("ERROR: not connected.")
			logger.debug(f"<<< _on_read (not connected)")
			return
		try:
			value=self._instr_ctrl.read()
			print(value) # REMOVE
			self._view.set_read(value)
			logger.debug(f"<<< _on_read (value={value})")
		except Exception as e:
			self._view.set_status(f"Read error: {e}")
			logger.debug(f"<<< _on_read (error={e})")
	'''

	def _on_main_window_closed(self):
		self._trigger_base_pop_up.close()
		self._trigger_advanced_pop_up.close()
		self._acquisition.close()

	def _on_application_about_to_quit(self):
		self._acquisition.stop()
		if not self._instr_ctrl.is_connected():
			return

		try:
			self._instr_ctrl.disconnect()
		except Exception as error:
			logger.warning(f"Instrument disconnect on close failed: {error}")

	'''
	Legacy GPIB init and mode selection of the old GUI: replaced by
	_on_scan/_on_connect and by the function tabs of the view
	(current_gpib_address, current_mode and set_mode_visible no longer exist).
	def _on_init(self):
		logger.debug(f">>> _on_init (gpib_address={self._view.current_gpib_address})")
		if hasattr(self, '_instr_ctrl'):
			if self._instr_ctrl.is_connected():
				self._instr_ctrl.disconnect()
		self._instr_ctrl.connect(self._view.current_gpib_address)
		self._view.set_connected()
		self._view.set_status("Connected")
		logger.debug(f"<<< _on_init")
	
	def _on_mode_change(self):
		logger.debug(f">>> _on_mode_change (mode={self._view.current_mode})")
		self._view.set_mode_visible(self._view.current_mode)
		logger.debug(f"<<< _on_mode_change")
	'''

	'''
	Legacy generic SET/readback path. Active measurement handlers commit
	presenter settings after the instrument accepts the requested values.
	def _on_set(self):
		mode=self._view.current_mode
		logger.debug(f">>> _on_set (mode={mode})")
		new_settings=self.get_settings_from_mode(mode)
		logger.debug(f"    SEND_TO_INSTRUMENT: {new_settings}")
		actual_settings=self._instr_ctrl.set(mode, new_settings)
		logger.debug(f"    RECEIVED_FROM_INSTRUMENT: {actual_settings}")
		
		#Reverse-translate machine values back to GUI format
		if mode == "DCV":
			gui_settings = DcvSettings(
				range_mode=actual_settings.range_mode,
				range_val=self._translator.translate_reverse("dcv_range", actual_settings.range_val),
				resolution=actual_settings.resolution,
				zin=self._translator.translate_reverse("impedence", actual_settings.zin),
				aperture_mode=actual_settings.aperture_mode,
				time=actual_settings.time
			)
			self._dcv_settings = gui_settings
		elif mode == "DCI":
			gui_settings = DciSettings(
				range_mode=actual_settings.range_mode,
				range_val=self._translator.translate_reverse("dci_range", actual_settings.range_val),
				resolution=actual_settings.resolution,
				aperture_mode=actual_settings.aperture_mode,
				time=actual_settings.time
			)
			self._dci_settings = gui_settings
		elif mode == "OHMS":
			gui_settings = OhmsSettings(
				four=False,
				range_val=self._translator.translate_reverse("ohm_range", actual_settings.range_val),
				resolution=actual_settings.resolution,
				mode=self._translator.translate_reverse("ohm_mode", actual_settings.mode),
				filter=actual_settings.filter,
				low_i=actual_settings.low_i,
				aperture_mode=actual_settings.aperture_mode,
				time=actual_settings.time
			)
			self._ohms_settings = gui_settings
		
		# Update the GUI to reflect actual settings
		logger.debug(f"    REVERSE_TRANSLATED: {gui_settings}")
		self._view.set_status(f"{mode} settings applied")
		self._refresh_ui_settings()
		logger.debug(f"<<< _on_set")
	'''

	'''
	Unused: only called by the commented _on_set and aperture handlers, and
	the view has no current_mode anymore.
	def get_settings_from_mode(self, mode: str):
		if mode == "DCV":
			return self._dcv_settings
		if mode == "DCI":
			return self._dci_settings
		if mode == "OHMS":
			return self._ohms_settings
	
	def _refresh_ui_settings(self):
		"""Update UI to show current settings from app controller"""
		mode = self._view.current_mode
		if mode == "DCV":
			self._view.set_dcv_settings(self._dcv_settings)
		elif mode == "DCI":
			self._view.set_dci_settings(self._dci_settings)
		elif mode == "OHMS":
			self._view._on_ohms_settings_received(self._ohms_settings)
	'''

	'''
	Unused: the advanced trigger window (self._trigger_pop_up) is not created yet.
	def _on_trigger_press(self):
		logger.debug(f">>> _on_trigger_press")
		self._trigger_pop_up.show()
		logger.debug(f"<<< _on_trigger_press")
	'''

	def _on_trigger_base_press(self):
		logger.debug(f">>> _on_trigger_base_press")
		self._trigger_base_pop_up.show()
		logger.debug(f"<<< _on_trigger_base_press")

	def _on_trigger_base_set(self):
		self._acquisition.stop()
		settings = self._trigger_base_pop_up.get_settings()
		try:
			actual = self._instr_ctrl.set_trigger_base(self._translate_trigger_base_settings(settings))
			self._set_trigger_base_settings(self._translate_trigger_base_settings_to_gui(actual))
			self._set_trigger_advanced_settings(self._advanced_with_base_trigger(
				self._trigger_advanced_settings, self._trigger_base_settings
			))
			self._trigger_base_pop_up.close()
			self._view.set_status("Base trigger settings applied")
		except Exception as error:
			self._view.set_status(f"Base trigger error: {error}")

	def _on_trigger_base_reset(self):
		self._acquisition.stop()
		# GUI state changes only once the instrument has accepted the reset
		base = defaults.trigger_base_settings()
		# :TRIG:RESet resets the ARM layers too, but not INIT:CONT
		current = self._trigger_advanced_settings
		advanced = replace(
			defaults.trigger_advanced_settings(),
			initiate_mode=current.initiate_mode,
			epoch_start=current.epoch_start,
			epoch_stop=current.epoch_stop,
		)
		try:
			self._instr_ctrl.reset_trigger_base()
			actual = self._instr_ctrl.set_trigger_base(self._translate_trigger_base_settings(base))
			self._set_trigger_base_settings(self._translate_trigger_base_settings_to_gui(actual))
			self._set_trigger_advanced_settings(self._advanced_with_base_trigger(
				advanced, self._trigger_base_settings
			))
			self._view.set_status("Base trigger reset")
		except Exception as error:
			self._view.set_status(f"Base trigger reset error: {error}{self._refresh_trigger_settings()}")

	def _translate_trigger_base_settings(self, settings: TriggerBaseSettings) -> TriggerBaseSettings:
		return replace(
			settings,
			source=self._translator.translate("trigger_source", settings.source),
			ext_edge=(
				None
				if settings.ext_edge is None
				else self._translator.translate("trigger_external_edge", settings.ext_edge)
			),
		)

	def _translate_trigger_base_settings_to_gui(self, settings: TriggerBaseSettings) -> TriggerBaseSettings:
		return replace(
			settings,
			source=self._translator.translate_from_machine("trigger_source", settings.source),
			ext_edge=(
				None
				if settings.ext_edge is None
				else self._translator.translate_from_machine("trigger_external_edge", settings.ext_edge)
			),
		)

	def _on_trigger_advanced_press(self):
		logger.debug(f">>> _on_trigger_advanced_press")
		self._trigger_advanced_pop_up.show()
		logger.debug(f"<<< _on_trigger_advanced_press")

	def _on_trigger_advanced_set(self):
		self._acquisition.stop()
		settings = self._trigger_advanced_pop_up.get_settings()
		try:
			actual = self._instr_ctrl.set_trigger_advanced(self._translate_trigger_advanced_settings(settings))
			self._set_trigger_advanced_settings(self._translate_trigger_advanced_settings_to_gui(actual))
			self._set_trigger_base_settings(self._base_with_advanced_trigger(
				self._trigger_base_settings, self._trigger_advanced_settings
			))
			self._trigger_advanced_pop_up.close()
			self._view.set_status("Advanced trigger settings applied")
		except Exception as error:
			self._view.set_status(f"Advanced trigger error: {error}")

	def _on_trigger_advanced_reset(self):
		self._acquisition.stop()
		# GUI state changes only once the instrument has accepted the reset
		advanced = defaults.trigger_advanced_settings()
		try:
			self._instr_ctrl.reset_trigger_base()
			actual = self._instr_ctrl.set_trigger_advanced(self._translate_trigger_advanced_settings(advanced))
			self._set_trigger_advanced_settings(self._translate_trigger_advanced_settings_to_gui(actual))
			self._set_trigger_base_settings(self._base_with_advanced_trigger(
				defaults.trigger_base_settings(), self._trigger_advanced_settings
			))
			self._view.set_status("Advanced trigger reset")
		except Exception as error:
			self._view.set_status(f"Advanced trigger reset error: {error}{self._refresh_trigger_settings()}")

	def _refresh_trigger_settings(self) -> str:
		"""
		After a failed reset the instrument may be half reset: read the layers
		back so the GUI follows it. Returns a note for the status bar.
		"""
		try:
			actual = self._instr_ctrl.get_trigger_advanced(
				self._translate_trigger_advanced_settings(self._trigger_advanced_settings)
			)
		except Exception as error:
			logger.debug(f"_refresh_trigger_settings (error={error})")
			return " (trigger state could not be read back, the GUI may not match the instrument)"
		self._set_trigger_advanced_settings(self._translate_trigger_advanced_settings_to_gui(actual))
		self._set_trigger_base_settings(self._base_with_advanced_trigger(
			self._trigger_base_settings, self._trigger_advanced_settings
		))
		return " (trigger state read back from the instrument)"

	def _translate_trigger_advanced_settings(self, settings: TriggerAdvancedSettings) -> TriggerAdvancedSettings:
		return replace(
			settings,
			initiate_mode=self._translator.translate("trigger_initiate_mode", settings.initiate_mode),
			ext_edge=self._translator.translate("trigger_external_edge", settings.ext_edge),
			arm2=self._translate_trigger_layer(settings.arm2),
			arm1=self._translate_trigger_layer(settings.arm1),
			trigger=self._translate_trigger_layer(settings.trigger),
		)

	def _translate_trigger_advanced_settings_to_gui(self, settings: TriggerAdvancedSettings) -> TriggerAdvancedSettings:
		return replace(
			settings,
			initiate_mode=self._translator.translate_from_machine("trigger_initiate_mode", settings.initiate_mode),
			ext_edge=self._translator.translate_from_machine("trigger_external_edge", settings.ext_edge),
			arm2=self._translate_trigger_layer_to_gui(settings.arm2),
			arm1=self._translate_trigger_layer_to_gui(settings.arm1),
			trigger=self._translate_trigger_layer_to_gui(settings.trigger),
		)

	# The base window edits the TRIG layer of the advanced one: keep the two in step
	def _set_trigger_base_settings(self, settings: TriggerBaseSettings) -> None:
		self._trigger_base_settings = settings
		self._trigger_base_pop_up.set_settings(settings)

	def _set_trigger_advanced_settings(self, settings: TriggerAdvancedSettings) -> None:
		self._trigger_advanced_settings = settings
		self._trigger_advanced_pop_up.set_settings(settings)

	def _advanced_with_base_trigger(
		self, advanced: TriggerAdvancedSettings, base: TriggerBaseSettings
	) -> TriggerAdvancedSettings:
		"""Advanced settings with the TRIG layer, edge and signal sent by the base trigger."""
		trigger = replace(
			advanced.trigger,
			source=base.source,
			count=base.count,
			ecount=base.ecount,
			delay=base.delay,
			delay_auto=base.delay_auto,
			holdoff=base.holdoff,
			holdoff_auto=base.holdoff_auto,
		)
		# The base trigger sends timer, edge and signal only for their source
		if base.source == gui_values.TRIGGER_SOURCE_TIMER:
			trigger = replace(trigger, timer=base.timer)
		advanced = replace(advanced, trigger=trigger)
		if base.source == gui_values.TRIGGER_SOURCE_EXTERNAL:
			advanced = replace(advanced, ext_edge=base.ext_edge)
		if base.source == gui_values.TRIGGER_SOURCE_INTERNAL:
			advanced = replace(advanced, signal=TriggerSignalSettings(
				coupling=base.sig_coupling,
				slope=base.sig_slope,
				level=base.sig_level,
				filter=base.sig_filter,
			))
		return advanced

	def _base_with_advanced_trigger(
		self, base: TriggerBaseSettings, advanced: TriggerAdvancedSettings
	) -> TriggerBaseSettings:
		"""Base settings showing the TRIG layer, edge and signal of the advanced trigger."""
		trigger = advanced.trigger
		return replace(
			base,
			source=trigger.source,
			count=trigger.count,
			ecount=trigger.ecount,
			delay=trigger.delay,
			delay_auto=trigger.delay_auto,
			holdoff=trigger.holdoff,
			holdoff_auto=trigger.holdoff_auto,
			timer=trigger.timer,
			ext_edge=advanced.ext_edge,
			sig_coupling=advanced.signal.coupling,
			sig_slope=advanced.signal.slope,
			sig_level=advanced.signal.level,
			sig_filter=advanced.signal.filter,
		)

	def _translate_trigger_layer(self, layer: TriggerLayerSettings) -> TriggerLayerSettings:
		# replace keeps the subclass, so the TRIG layer keeps its holdoff
		return replace(layer, source=self._translator.translate("trigger_source", layer.source))

	def _translate_trigger_layer_to_gui(self, layer: TriggerLayerSettings) -> TriggerLayerSettings:
		return replace(layer, source=self._translator.translate_from_machine("trigger_source", layer.source))
			
	'''
	Legacy aperture handlers of the old GUI: replaced by _on_aperture_value_changed,
	the view methods they call (set_aperture_mode, set_time_value,
	set_nplc_value) no longer exist.
	def _on_aperture_mode_changed(self, mode):
		logger.debug(f">>> _on_aperture_mode_changed (mode={mode})")
		self._view.set_aperture_mode(mode)
		current_mode = self._view.current_mode
		settings = self.get_settings_from_mode(current_mode)
		settings.aperture_mode = mode
		logger.debug(f"<<< _on_aperture_mode_changed")

	def _on_time_changed(self, time):
		logger.debug(f">>> _on_time_changed (time={time})")
		self._view.set_time_value(time)
		current_mode = self._view.current_mode
		settings = self.get_settings_from_mode(current_mode)
		settings.time = time
		logger.debug(f"<<< _on_time_changed")

	def _on_nplc_changed(self, nplc):
		# NPLC is handled via _on_time_changed (same value, different units)
		# This just updates the display label for reference
		logger.debug(f">>> _on_nplc_changed (nplc={nplc})")
		self._current_nplc = nplc
		self._view.set_nplc_value(nplc)
		logger.debug(f"<<< _on_nplc_changed")
	'''

	def calculate_plc(self, time: float) -> float:
		if self._line_frequency is None:
			raise RuntimeError("Cannot calculate NPLC: instrument is not connected")
		return float(time) * self._line_frequency

	def calculate_time(self, plc: float) -> float:
		if self._line_frequency is None:
			raise RuntimeError("Cannot calculate time: instrument is not connected")
		return float(plc) / self._line_frequency

	def _update_view_aperture_values(self):
		if self._line_frequency is None:
			return
		for function, settings in (
			("DCV", self._dcv_settings),
			("DCI", self._dci_settings),
			("OHMS", self._ohms_settings),
		):
			self._view.set_aperture_values(
				function,
				settings.time,
				self.calculate_plc(settings.time),
			)

	def _on_aperture_value_changed(self, function: str, source: str, value: float):
		# Only keeps time and PLC in sync in the view: the stored settings hold
		# the values applied to the instrument, the edits are read on start
		if self._line_frequency is None:
			return
		if source == "time":
			time = float(value)
			plc = self.calculate_plc(time)
		else:
			plc = float(value)
			time = self.calculate_time(plc)
		self._view.set_aperture_values(function, time, plc)

	'''
	Legacy, same as the aperture handlers above.
	def _set_ui_aperture_settings(self):
		self._view.set_aperture_mode()
		self._view.set_time_value()
	'''
		
	
	def _translate_dcv_settings(self, settings: DcvSettings) -> DcvSettings:
		# With autorange the resolution is written on a reference range, then
		# the instrument keeps the digits when it changes range
		resolution_range = (
			tables.DCV_AUTO_REFERENCE_RANGE
			if settings.range_mode == gui_values.RANGE_MODE_AUTO
			else settings.range_val
		)
		return DcvSettings(
			range_mode=self._translator.translate("range_mode", settings.range_mode),
			range_val=self._translator.translate("dcv_range", resolution_range),
			resolution=self._translator.translate_resolution(
				settings.resolution,
				gui_values.DCV_RESOLUTION_DIGITS[1],
				self._translator.translate("dcv_max_resolution", resolution_range),
			),
			zin=self._translator.translate("dcv_impedance", settings.zin),
			aperture_mode=self._translator.translate("aperture_mode", settings.aperture_mode),
			time=settings.time,
		)

	def _translate_dci_settings(self, settings: DciSettings) -> DciSettings:
		# With autorange the resolution is written on a reference range, then
		# the instrument keeps the digits when it changes range
		resolution_range = (
			tables.DCI_AUTO_REFERENCE_RANGE
			if settings.range_mode == gui_values.RANGE_MODE_AUTO
			else settings.range_val
		)
		return DciSettings(
			range_mode=self._translator.translate("range_mode", settings.range_mode),
			range_val=self._translator.translate("dci_range", resolution_range),
			resolution=self._translator.translate_resolution(
				settings.resolution,
				gui_values.DCI_RESOLUTION_DIGITS[1],
				self._translator.translate("dci_max_resolution", resolution_range),
			),
			aperture_mode=self._translator.translate("aperture_mode", settings.aperture_mode),
			time=settings.time,
		)

	def _translate_acv_settings(self, settings: AcvSettings) -> AcvSettings:
		# With autorange the resolution is written on a reference range, then
		# the instrument keeps the digits when it changes range
		resolution_range = (
			tables.ACV_AUTO_REFERENCE_RANGE
			if settings.range_mode == gui_values.RANGE_MODE_AUTO
			else settings.range_val
		)
		return AcvSettings(
			range_mode=self._translator.translate("range_mode", settings.range_mode),
			range_val=self._translator.translate("acv_range", resolution_range),
			resolution=self._translator.translate_resolution(
				settings.resolution,
				gui_values.AC_RESOLUTION_DIGITS[1],
				self._translator.translate("acv_max_resolution", resolution_range),
			),
			rms_filter=self._translator.translate("ac_rms_filter", settings.rms_filter),
			coupling_impedance=self._translator.translate("acv_coupling_impedance", settings.coupling_impedance),
			secondary_reading=self._translator.translate("ac_secondary_reading", settings.secondary_reading),
			frequency_path_coupling=self._translator.translate("ac_path_coupling", settings.frequency_path_coupling),
			frequency_path_bandwidth_limit=self._translator.translate(
				"ac_bandwidth_limit", settings.frequency_path_bandwidth_limit
			),
			counter_gate=self._translator.translate("ac_counter_gate", settings.counter_gate),
			bandwidth=self._translator.translate("acv_bandwidth", settings.bandwidth),
			peak_to_peak=self._translator.translate("ac_peak_to_peak", settings.peak_to_peak),
		)

	def _translate_aci_settings(self, settings: AciSettings) -> AciSettings:
		# With autorange the resolution is written on a reference range, then
		# the instrument keeps the digits when it changes range
		resolution_range = (
			tables.ACI_AUTO_REFERENCE_RANGE
			if settings.range_mode == gui_values.RANGE_MODE_AUTO
			else settings.range_val
		)
		return AciSettings(
			range_mode=self._translator.translate("range_mode", settings.range_mode),
			range_val=self._translator.translate("aci_range", resolution_range),
			resolution=self._translator.translate_resolution(
				settings.resolution,
				gui_values.AC_RESOLUTION_DIGITS[1],
				self._translator.translate("aci_max_resolution", resolution_range),
			),
			rms_filter=self._translator.translate("ac_rms_filter", settings.rms_filter),
			signal_path_coupling=self._translator.translate("aci_signal_coupling", settings.signal_path_coupling),
			secondary_reading=self._translator.translate("ac_secondary_reading", settings.secondary_reading),
			frequency_path_coupling=self._translator.translate("ac_path_coupling", settings.frequency_path_coupling),
			frequency_path_bandwidth_limit=self._translator.translate(
				"ac_bandwidth_limit", settings.frequency_path_bandwidth_limit
			),
			counter_gate=self._translator.translate("ac_counter_gate", settings.counter_gate),
			peak_to_peak=self._translator.translate("ac_peak_to_peak", settings.peak_to_peak),
		)

	def _translate_ohms_settings(self, settings: OhmsSettings) -> OhmsSettings:
		# The resolution is always written on the reference range, then the
		# instrument keeps the digits on the manual range or in autorange
		range_val = (
			tables.OHM_AUTO_REFERENCE_RANGE
			if settings.range_mode == gui_values.RANGE_MODE_AUTO
			else settings.range_val
		)
		return OhmsSettings(
			range_mode=self._translator.translate("range_mode", settings.range_mode),
			range_val=self._translator.translate("ohm_range", range_val),
			resolution=self._translator.translate_resolution(
				settings.resolution,
				gui_values.OHMS_RESOLUTION_DIGITS[1],
				self._translator.translate("ohm_max_resolution", tables.OHM_AUTO_REFERENCE_RANGE),
			),
			mode=self._translator.translate("ohm_mode", settings.mode),
			filter=settings.filter,
			low_current=settings.low_current,
			aperture_mode=self._translator.translate("aperture_mode", settings.aperture_mode),
			time=settings.time,
		)

	def _translate_digitize_settings(self, settings: DigitizeSettings) -> DigitizeSettings:
		# Voltage and current have their own range and coupling tables
		prefix = "digi_v" if settings.signal == gui_values.DIGI_SIGNAL_VOLTAGE else "digi_i"
		return DigitizeSettings(
			signal=self._translator.translate("digi_signal", settings.signal),
			range_val=self._translator.translate(f"{prefix}_range", settings.range_val),
			coupling_impedance=self._translator.translate(
				f"{prefix}_coupling_impedance", settings.coupling_impedance
			),
			filter=self._translator.translate("digi_filter", settings.filter),
			aperture=settings.aperture,
		)

	def _on_dcv_set(self):
		self._acquisition.stop()
		logger.debug(">>> _on_dcv_set")
		try:
			requested_settings = self._translate_dcv_settings(self._view.get_dcv_settings())
			logger.debug(f"    SEND_TO_INSTRUMENT: {requested_settings}")
			actual_settings = self._instr_ctrl.set_dcv(requested_settings)
			logger.debug(f"    RECEIVED_FROM_INSTRUMENT: {actual_settings}")
			self._dcv_settings = self._translate_dcv_settings_to_gui(actual_settings)
			self._show_dcv_settings()
			self._view.set_status("DCV configured.")
			self._acquisition.show_function("DCV", self._dcv_settings)
			self._acquisition.show_range_unit("Voltage", "V", self._dcv_settings)
		except Exception as error:
			self._view.set_status(f"DCV set error: {error}")
			logger.debug(f"<<< _on_dcv_set (error={error})")
			return
		logger.debug("<<< _on_dcv_set")

	def _show_dcv_settings(self):
		"""Show the applied DCV settings (GUI format), PLC included when known."""
		self._view.set_dcv_settings(self._dcv_settings)
		if self._line_frequency is not None:
			self._view.set_aperture_values(
				"DCV",
				self._dcv_settings.time,
				self.calculate_plc(self._dcv_settings.time),
			)

	def _on_dci_set(self):
		self._acquisition.stop()
		logger.debug(">>> _on_dci_set")
		try:
			requested_settings = self._translate_dci_settings(self._view.get_dci_settings())
			logger.debug(f"    SEND_TO_INSTRUMENT: {requested_settings}")
			actual_settings = self._instr_ctrl.set_dci(requested_settings)
			logger.debug(f"    RECEIVED_FROM_INSTRUMENT: {actual_settings}")
			self._dci_settings = self._translate_dci_settings_to_gui(actual_settings)
			self._show_dci_settings()
			self._view.set_status("DCI configured.")
			self._acquisition.show_function("DCI", self._dci_settings)
			self._acquisition.show_range_unit("Current", "A", self._dci_settings)
		except Exception as error:
			self._view.set_status(f"DCI set error: {error}")
			logger.debug(f"<<< _on_dci_set (error={error})")
			return
		logger.debug("<<< _on_dci_set")

	def _show_dci_settings(self):
		"""Show the applied DCI settings (GUI format), PLC included when known."""
		self._view.set_dci_settings(self._dci_settings)
		if self._line_frequency is not None:
			self._view.set_aperture_values(
				"DCI",
				self._dci_settings.time,
				self.calculate_plc(self._dci_settings.time),
			)

	def _on_acv_set(self):
		self._acquisition.stop()
		logger.debug(">>> _on_acv_set")
		try:
			requested_settings = self._translate_acv_settings(self._view.get_acv_settings())
			logger.debug(f"    SEND_TO_INSTRUMENT: {requested_settings}")
			actual_settings = self._instr_ctrl.set_acv(requested_settings)
			logger.debug(f"    RECEIVED_FROM_INSTRUMENT: {actual_settings}")
			self._acv_settings = self._translate_acv_settings_to_gui(actual_settings)
			# ACV has no aperture, nothing else to show
			self._view.set_acv_settings(self._acv_settings)
			self._view.set_status("ACV configured.")
			self._show_ac_graph("ACV", "Voltage", "V", self._acv_settings)
		except Exception as error:
			self._view.set_status(f"ACV set error: {error}")
			logger.debug(f"<<< _on_acv_set (error={error})")
			return
		logger.debug("<<< _on_acv_set")

	def _on_aci_set(self):
		self._acquisition.stop()
		logger.debug(">>> _on_aci_set")
		try:
			requested_settings = self._translate_aci_settings(self._view.get_aci_settings())
			logger.debug(f"    SEND_TO_INSTRUMENT: {requested_settings}")
			actual_settings = self._instr_ctrl.set_aci(requested_settings)
			logger.debug(f"    RECEIVED_FROM_INSTRUMENT: {actual_settings}")
			self._aci_settings = self._translate_aci_settings_to_gui(actual_settings)
			# ACI has no aperture, nothing else to show
			self._view.set_aci_settings(self._aci_settings)
			self._view.set_status("ACI configured.")
			self._show_ac_graph("ACI", "Current", "A", self._aci_settings)
		except Exception as error:
			self._view.set_status(f"ACI set error: {error}")
			logger.debug(f"<<< _on_aci_set (error={error})")
			return
		logger.debug("<<< _on_aci_set")

	def _show_ac_graph(self, function: str, quantity: str, base_unit: str, settings) -> None:
		"""Graph of ACV/ACI: primary unit from the range, second graph for the secondary reading when ON."""
		secondary_reading = self._ac_secondary_reading(settings)
		self._acquisition.show_function(function, settings, secondary_reading)
		self._acquisition.show_range_unit(quantity, base_unit, settings)
		if secondary_reading is not None:
			self._acquisition.show_secondary_unit(*units.ac_secondary_unit(secondary_reading, base_unit))

	@staticmethod
	def _ac_secondary_reading(settings) -> str | None:
		"""GUI name of the AC secondary reading, None when it is OFF."""
		if settings.secondary_reading == gui_values.AC_SECREAD_OFF:
			return None
		return settings.secondary_reading

	def _on_ohms_set(self):
		self._acquisition.stop()
		logger.debug(">>> _on_ohms_set")
		try:
			requested_settings = self._translate_ohms_settings(self._view.get_ohms_settings())
			logger.debug(f"    SEND_TO_INSTRUMENT: {requested_settings}")
			actual_settings = self._instr_ctrl.set_ohms(requested_settings)
			logger.debug(f"    RECEIVED_FROM_INSTRUMENT: {actual_settings}")
			self._ohms_settings = self._translate_ohms_settings_to_gui(actual_settings)
			self._show_ohms_settings()
			self._view.set_status("OHMS configured.")
			self._acquisition.show_function("OHMS", self._ohms_settings)
			self._acquisition.show_range_unit("Resistance", "Ω", self._ohms_settings)
		except Exception as error:
			self._view.set_status(f"OHMS set error: {error}")
			logger.debug(f"<<< _on_ohms_set (error={error})")
			return
		logger.debug("<<< _on_ohms_set")

	def _on_digitize_set(self):
		self._acquisition.stop()
		logger.debug(">>> _on_digitize_set")
		try:
			requested_settings = self._translate_digitize_settings(self._view.get_digitize_settings())
			logger.debug(f"    SEND_TO_INSTRUMENT: {requested_settings}")
			actual_settings = self._instr_ctrl.set_digitize(requested_settings)
			logger.debug(f"    RECEIVED_FROM_INSTRUMENT: {actual_settings}")
			self._digitize_settings = self._translate_digitize_settings_to_gui(actual_settings)
			# The digitize aperture is a time only, no PLC to show
			self._view.set_digitize_settings(self._digitize_settings)
			self._view.set_status("DIGITIZE configured.")
			self._acquisition.show_function("DIGITIZE", self._digitize_settings)
		except Exception as error:
			self._view.set_status(f"DIGITIZE set error: {error}")
			logger.debug(f"<<< _on_digitize_set (error={error})")
			return
		logger.debug("<<< _on_digitize_set")

	def _show_ohms_settings(self):
		"""Show the applied OHMS settings (GUI format), PLC included when known."""
		self._view.set_ohms_settings(self._ohms_settings)
		if self._line_frequency is not None:
			self._view.set_aperture_values(
				"OHMS",
				self._ohms_settings.time,
				self.calculate_plc(self._ohms_settings.time),
			)

	def _translate_dcv_settings_to_gui(self, settings: DcvSettings) -> DcvSettings:
		return DcvSettings(
			range_mode=self._translator.translate_from_machine("range_mode", settings.range_mode),
			range_val=(
				gui_values.AUTO
				if settings.range_mode == scpi.RANGE_MODE_AUTO_STR
				else self._translator.translate_from_machine("dcv_range", settings.range_val)
			),
			# range_val is the range actually in use, also with auto range
			resolution=self._translator.translate_resolution_from_machine(
				settings.resolution,
				gui_values.DCV_RESOLUTION_DIGITS[1],
				self._translator.translate(
					"dcv_max_resolution",
					self._translator.translate_from_machine("dcv_range", settings.range_val),
				),
			),
			zin=self._translator.translate_from_machine("dcv_impedance", settings.zin),
			aperture_mode=self._translator.translate_from_machine("aperture_mode", settings.aperture_mode),
			time=settings.time,
		)

	def _translate_dci_settings_to_gui(self, settings: DciSettings) -> DciSettings:
		return DciSettings(
			range_mode=self._translator.translate_from_machine("range_mode", settings.range_mode),
			range_val=(
				gui_values.AUTO
				if settings.range_mode == scpi.RANGE_MODE_AUTO_STR
				else self._translator.translate_from_machine("dci_range", settings.range_val)
			),
			# range_val is the range actually in use, also with auto range
			resolution=self._translator.translate_resolution_from_machine(
				settings.resolution,
				gui_values.DCI_RESOLUTION_DIGITS[1],
				self._translator.translate(
					"dci_max_resolution",
					self._translator.translate_from_machine("dci_range", settings.range_val),
				),
			),
			aperture_mode=self._translator.translate_from_machine("aperture_mode", settings.aperture_mode),
			time=settings.time,
		)

	def _translate_acv_settings_to_gui(self, settings: AcvSettings) -> AcvSettings:
		return AcvSettings(
			range_mode=self._translator.translate_from_machine("range_mode", settings.range_mode),
			range_val=(
				gui_values.AUTO
				if settings.range_mode == scpi.RANGE_MODE_AUTO_STR
				else self._translator.translate_from_machine("acv_range", settings.range_val)
			),
			# range_val is the range actually in use, also with auto range
			resolution=self._translator.translate_resolution_from_machine(
				settings.resolution,
				gui_values.AC_RESOLUTION_DIGITS[1],
				self._translator.translate(
					"acv_max_resolution",
					self._translator.translate_from_machine("acv_range", settings.range_val),
				),
			),
			rms_filter=self._translator.translate_from_machine("ac_rms_filter", settings.rms_filter),
			coupling_impedance=self._translator.translate_from_machine("acv_coupling_impedance", settings.coupling_impedance),
			secondary_reading=self._translator.translate_from_machine("ac_secondary_reading", settings.secondary_reading),
			frequency_path_coupling=self._translator.translate_from_machine("ac_path_coupling", settings.frequency_path_coupling),
			frequency_path_bandwidth_limit=self._translator.translate_from_machine(
				"ac_bandwidth_limit", settings.frequency_path_bandwidth_limit
			),
			counter_gate=self._translator.translate_from_machine("ac_counter_gate", settings.counter_gate),
			bandwidth=self._translator.translate_from_machine("acv_bandwidth", settings.bandwidth),
			peak_to_peak=self._translator.translate_from_machine("ac_peak_to_peak", settings.peak_to_peak),
		)

	def _translate_aci_settings_to_gui(self, settings: AciSettings) -> AciSettings:
		return AciSettings(
			range_mode=self._translator.translate_from_machine("range_mode", settings.range_mode),
			range_val=(
				gui_values.AUTO
				if settings.range_mode == scpi.RANGE_MODE_AUTO_STR
				else self._translator.translate_from_machine("aci_range", settings.range_val)
			),
			# range_val is the range actually in use, also with auto range
			resolution=self._translator.translate_resolution_from_machine(
				settings.resolution,
				gui_values.AC_RESOLUTION_DIGITS[1],
				self._translator.translate(
					"aci_max_resolution",
					self._translator.translate_from_machine("aci_range", settings.range_val),
				),
			),
			rms_filter=self._translator.translate_from_machine("ac_rms_filter", settings.rms_filter),
			signal_path_coupling=self._translator.translate_from_machine("aci_signal_coupling", settings.signal_path_coupling),
			secondary_reading=self._translator.translate_from_machine("ac_secondary_reading", settings.secondary_reading),
			frequency_path_coupling=self._translator.translate_from_machine("ac_path_coupling", settings.frequency_path_coupling),
			frequency_path_bandwidth_limit=self._translator.translate_from_machine(
				"ac_bandwidth_limit", settings.frequency_path_bandwidth_limit
			),
			counter_gate=self._translator.translate_from_machine("ac_counter_gate", settings.counter_gate),
			peak_to_peak=self._translator.translate_from_machine("ac_peak_to_peak", settings.peak_to_peak),
		)

	def _translate_ohms_settings_to_gui(self, settings: OhmsSettings) -> OhmsSettings:
		range_label = self._translator.translate_from_machine("ohm_range", settings.range_val)
		return OhmsSettings(
			range_mode=self._translator.translate_from_machine("range_mode", settings.range_mode),
			range_val=(
				gui_values.AUTO
				if settings.range_mode == scpi.RANGE_MODE_AUTO_STR
				else range_label
			),
			# range_val is the range actually in use, also with auto range
			resolution=self._translator.translate_resolution_from_machine(
				settings.resolution,
				gui_values.OHMS_RESOLUTION_DIGITS[1],
				self._translator.translate("ohm_max_resolution", range_label),
			),
			mode=self._translator.translate_from_machine("ohm_mode", settings.mode),
			filter=settings.filter,
			low_current=settings.low_current,
			aperture_mode=self._translator.translate_from_machine("aperture_mode", settings.aperture_mode),
			time=settings.time,
		)

	def _translate_digitize_settings_to_gui(self, settings: DigitizeSettings) -> DigitizeSettings:
		prefix = "digi_v" if settings.signal == scpi.DIGI_VOLTAGE else "digi_i"
		return DigitizeSettings(
			signal=self._translator.translate_from_machine("digi_signal", settings.signal),
			range_val=self._translator.translate_from_machine(f"{prefix}_range", settings.range_val),
			coupling_impedance=self._translator.translate_from_machine(
				f"{prefix}_coupling_impedance", settings.coupling_impedance
			),
			filter=self._translator.translate_from_machine("digi_filter", settings.filter),
			aperture=settings.aperture,
		)

	'''
	Unused: continuous reading of the old GUI, replaced by
	AcquisitionController (Start/Stop of the graph window).
	def _on_continuous_start(self):
		logger.debug(f">>> _on_continuous_start")
		if self._reading_thread is not None:
			logger.debug(f"<<< _on_continuous_start (thread already running)")
			return
		self._reading_thread=ReadingThread(self._instr_ctrl)
		self._reading_thread.reading_ready.connect(self._view.set_read) #emits from measurment_controller are redirected to view
		self._reading_thread.start()
		self._view.start_button.setEnabled(False)
		self._view.stop_button.setEnabled(True)
		self._view.set_status("Continuous reading started.")
		logger.debug(f"<<< _on_continuous_start")
		

	def _on_continuous_stop(self):
		logger.debug(f">>> _on_continuous_stop")
		if self._reading_thread is None:
			logger.debug(f"<<< _on_continuous_stop (no thread running)")
			return True
		self._reading_thread.stop()
		self._reading_thread = None
		self._view.set_status("Stopped.")
		self._view.stop_button.setEnabled(False)
		self._view.start_button.setEnabled(True)
		logger.debug(f"<<< _on_continuous_stop")
	'''

	def _on_scan(self):
		logger.debug(">>> _on_scan")
		try:
			resources = self._instr_ctrl.scan_resources()
			self._view.set_scan_results(resources)
			self._view.set_status(f"Found {len(resources)} VISA resource(s)")
			logger.debug(f"    VISA_RESOURCES: {resources}")
		except Exception as error:
			self._view.set_scan_results([])
			self._view.set_status(f"Scan error: {error}")
			logger.debug(f"    SCAN_ERROR: {error}")
		logger.debug("<<< _on_scan")

	def _on_connect(self, address: str):
		logger.debug(f">>> _on_connect (address={address})")
		try:
			self._instr_ctrl.connect(address)
			# Line frequency is read once per connection; the NPLC limits derive from it
			self._line_frequency = self._instr_ctrl.get_line_frequency()
			for function, min_time in (
				("DCV", scpi.APERTURE_TIME_MIN),
				("DCI", scpi.APERTURE_TIME_MIN),
				("OHMS", scpi.OHMS_APERTURE_TIME_MIN),
			):
				self._view.set_aperture_ranges(
					function,
					min_time,
					scpi.APERTURE_TIME_MAX,
					self.calculate_plc(min_time),
					self.calculate_plc(scpi.APERTURE_TIME_MAX),
				)
			# The connection resets the instrument (*RST), back to the defaults
			self._dcv_settings = defaults.dcv_settings()
			self._view.set_dcv_settings(self._dcv_settings)
			self._dci_settings = defaults.dci_settings()
			self._view.set_dci_settings(self._dci_settings)
			self._acv_settings = defaults.acv_settings()
			self._view.set_acv_settings(self._acv_settings)
			self._aci_settings = defaults.aci_settings()
			self._view.set_aci_settings(self._aci_settings)
			self._ohms_settings = defaults.ohms_settings()
			self._view.set_ohms_settings(self._ohms_settings)
			self._digitize_settings = defaults.digitize_settings()
			self._view.set_digitize_settings(self._digitize_settings)
			self._set_trigger_base_settings(defaults.trigger_base_settings())
			self._set_trigger_advanced_settings(defaults.trigger_advanced_settings())
			self._update_view_aperture_values()
			self._view.set_connected()
			self._view.set_status(f"Connected to {address}")
			logger.debug(f"<<< _on_connect (connected={address})")
		except Exception as error:
			self._view.set_status(f"Connection error: {error}")
			logger.debug(f"<<< _on_connect (error={error})")

	def _on_disconnect(self):
		self._acquisition.stop()
		logger.debug(">>> _on_disconnect")
		if not self._instr_ctrl.is_connected():
			self._view.set_disconnected()
			return

		try:
			self._instr_ctrl.disconnect()
			self._line_frequency = None
			self._view.set_disconnected()
			self._view.set_status("Disconnected")
			logger.debug("<<< _on_disconnect")
		except Exception as error:
			self._view.set_status(f"Disconnect error: {error}")
			logger.debug(f"<<< _on_disconnect (error={error})")