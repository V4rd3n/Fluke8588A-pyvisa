from Fluke8588A.controllers.instrument_controller import InstrumentController as InstrumentController 
from Fluke8588A.instrument import scpi
from Fluke8588A.data import defaults, gui_values
from Fluke8588A.views.main_window import MainWindow  
from Fluke8588A.views.trigger_base import TriggerBaseWindow
from Fluke8588A.data.settings import (
	AciSettings,
	AcvSettings,
	DciSettings,
	DcvSettings,
	OhmsSettings,
	TriggerBaseSettings,
)
from Fluke8588A.controllers.measurement_controller import ReadingThread
from Fluke8588A.services.translator import Translator
from Fluke8588A.services import translation_tables as tables
from PyQt6.QtWidgets import QApplication
from dataclasses import replace
class AppController:
	TEST_MODE = True  # Set to False to disable debug output
	
	def __init__(self):
		self._view = MainWindow()
		self._trigger_base_pop_up = TriggerBaseWindow()
		# self._trigger_pop_up = TriggerWindow()
		# self._view.set_disconnected()
		# The instrument is reset on connection, so the GUI starts from the defaults
		self._dcv_settings = defaults.dcv_settings()
		self._dci_settings = defaults.dci_settings()
		self._acv_settings = defaults.acv_settings()
		self._aci_settings = defaults.aci_settings()
		self._ohms_settings = defaults.ohms_settings()
		self._trigger_base_settings = defaults.trigger_base_settings()
		self._trigger_base_pop_up.set_settings(self._trigger_base_settings)
		
		self._connect_signals()
		QApplication.instance().aboutToQuit.connect(
			self._on_application_about_to_quit
		)
		self._view.show()
		self._instr_ctrl=InstrumentController()
		self._line_frequency = None
		self._reading_thread= None
		self._translator = Translator()
		self._pre_translate_defaults()

	def _pre_translate_defaults(self):
		"""Translate default GUI settings to machine format upon initialization."""
		if self.TEST_MODE: print(">>> _pre_translate_defaults")
		self._view.set_dcv_settings(self._dcv_settings)
		self._view._on_dci_settings_received(self._dci_settings)
		self._view._on_acv_settings_received(self._acv_settings)
		self._view._on_aci_settings_received(self._aci_settings)
		self._view._on_ohms_settings_received(self._ohms_settings)
		self._update_view_aperture_values()
		self._on_dci_setting_change(self._dci_settings)
		self._on_ohms_setting_change(self._ohms_settings)
		if self.TEST_MODE: print("<<< _pre_translate_defaults")

	def _connect_signals(self):
		self._view.scan_requested.connect(self._on_scan)
		self._view.connect_requested.connect(self._on_connect)
		self._view.disconnect_requested.connect(self._on_disconnect)
		self._view.dcv_start_requested.connect(self._on_dcv_start)
		self._view.dci_start_requested.connect(self._on_dci_start)
		self._view.trigger_base_requested.connect(self._on_trigger_base_press)
		self._trigger_base_pop_up.set_requested.connect(self._on_trigger_base_set)
		self._trigger_base_pop_up.reset_requested.connect(self._on_trigger_base_reset)
		self._view.aperture_value_changed.connect(self._on_aperture_value_changed)
		""" self._view.init_requested.connect(self._on_init)
		self._view.mode_changed.connect(self._on_mode_change)
		self._view.read_requested.connect(self._on_read)
		self._view.set_requested.connect(self._on_set)
		self._view.dcv_signal.connect(self._on_dcv_setting_change)
		self._view.dci_signal.connect(self._on_dci_setting_change)
		self._view.ohms_signal.connect(self._on_ohms_setting_change)
		self._view.continuous_start_requested.connect(self._on_continuous_start)
		self._view.continuous_stop_requested.connect(self._on_continuous_stop) """

	def _on_read(self):
		if self.TEST_MODE: print(f">>> _on_read")
		if not self._instr_ctrl.is_connected():
			self._view.set_status("ERROR: not connected.")
			if self.TEST_MODE: print(f"<<< _on_read (not connected)")
			return
		try:
			value=self._instr_ctrl.read()
			print(value) # REMOVE
			self._view.set_read(value)
			if self.TEST_MODE: print(f"<<< _on_read (value={value})")
		except Exception as e:
			self._view.set_status(f"Read error: {e}")
			if self.TEST_MODE: print(f"<<< _on_read (error={e})")	
	
	def _on_application_about_to_quit(self):
		if not self._instr_ctrl.is_connected():
			return

		try:
			self._instr_ctrl.disconnect()
		except Exception as error:
			if self.TEST_MODE:
				print(f"Instrument disconnect on close failed: {error}")

	def _on_init(self):
		if self.TEST_MODE: print(f">>> _on_init (gpib_address={self._view.current_gpib_address})")
		if hasattr(self, '_instr_ctrl'):
			if self._instr_ctrl.is_connected():
				self._instr_ctrl.disconnect()
		self._instr_ctrl.connect(self._view.current_gpib_address)
		self._view.set_connected()
		self._view.set_status("Connected")
		if self.TEST_MODE: print(f"<<< _on_init")
	
	def _on_mode_change(self):
		if self.TEST_MODE: print(f">>> _on_mode_change (mode={self._view.current_mode})")
		self._view.set_mode_visible(self._view.current_mode)
		if self.TEST_MODE: print(f"<<< _on_mode_change")

	'''
	Legacy generic SET/readback path. Active measurement handlers commit
	presenter settings after the instrument accepts the requested values.
	def _on_set(self):
		mode=self._view.current_mode
		if self.TEST_MODE: print(f">>> _on_set (mode={mode})")
		new_settings=self.get_settings_from_mode(mode)
		if self.TEST_MODE: print(f"    SEND_TO_INSTRUMENT: {new_settings}")
		actual_settings=self._instr_ctrl.set(mode, new_settings)
		if self.TEST_MODE: print(f"    RECEIVED_FROM_INSTRUMENT: {actual_settings}")
		
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
		if self.TEST_MODE: print(f"    REVERSE_TRANSLATED: {gui_settings}")
		self._view.set_status(f"{mode} settings applied")
		self._refresh_ui_settings()
		if self.TEST_MODE: print(f"<<< _on_set")
	'''

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
			self._view._on_dci_settings_received(self._dci_settings)
		elif mode == "OHMS":
			self._view._on_ohms_settings_received(self._ohms_settings)

	def _on_trigger_press(self):
		if self.TEST_MODE: print(f">>> _on_trigger_press")
		self._trigger_pop_up.show()
		if self.TEST_MODE: print(f"<<< _on_trigger_press")

	def _on_trigger_base_press(self):
		if self.TEST_MODE: print(f">>> _on_trigger_base_press")
		self._trigger_base_pop_up.show()
		if self.TEST_MODE: print(f"<<< _on_trigger_base_press")

	def _on_trigger_base_set(self):
		settings = self._trigger_base_pop_up.get_settings()
		try:
			self._instr_ctrl.set_trigger_base(self._translate_trigger_base_settings(settings))
			self._trigger_base_settings = settings
			self._trigger_base_pop_up.close()
			self._view.set_status("Base trigger settings applied")
		except Exception as error:
			self._view.set_status(f"Base trigger error: {error}")

	def _on_trigger_base_reset(self):
		self._trigger_base_settings = defaults.trigger_base_settings()
		self._trigger_base_pop_up.set_settings(self._trigger_base_settings)
		try:
			self._instr_ctrl.reset_trigger_base()
			self._instr_ctrl.set_trigger_base(
				self._translate_trigger_base_settings(self._trigger_base_settings)
			)
			self._view.set_status("Base trigger reset")
		except Exception as error:
			self._view.set_status(f"Base trigger reset error: {error}")

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
			
	def _on_aperture_mode_changed(self, mode):
		if self.TEST_MODE: print(f">>> _on_aperture_mode_changed (mode={mode})")
		self._view.set_aperture_mode(mode)
		current_mode = self._view.current_mode
		settings = self.get_settings_from_mode(current_mode)
		settings.aperture_mode = mode
		if self.TEST_MODE: print(f"<<< _on_aperture_mode_changed")

	def _on_time_changed(self, time):
		if self.TEST_MODE: print(f">>> _on_time_changed (time={time})")
		self._view.set_time_value(time)
		current_mode = self._view.current_mode
		settings = self.get_settings_from_mode(current_mode)
		settings.time = time
		if self.TEST_MODE: print(f"<<< _on_time_changed")

	def _on_nplc_changed(self, nplc):
		# NPLC is handled via _on_time_changed (same value, different units)
		# This just updates the display label for reference
		if self.TEST_MODE: print(f">>> _on_nplc_changed (nplc={nplc})")
		self._current_nplc = nplc
		self._view.set_nplc_value(nplc)
		if self.TEST_MODE: print(f"<<< _on_nplc_changed")

	def calculate_plc(self, time: float) -> float:
		if self._line_frequency is None:
			raise RuntimeError("Cannot calculate NPLC: instrument is not connected")
		return max(float(time) * self._line_frequency, scpi.NPLC_MIN)

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

	def _set_ui_aperture_settings(self):
		self._view.set_aperture_mode()
		self._view.set_time_value()
		
	
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

	def _on_dci_setting_change(self, settings: DciSettings):
		if self.TEST_MODE: print(f">>> _on_dci_setting_change (range_val={settings.range_val}, resolution={settings.resolution})")
		translated_settings = self._translate_dci_settings(settings)
		if self.TEST_MODE: print(f"    TRANSLATED: range_val={translated_settings.range_val}")
		self._dci_settings = translated_settings
		if self.TEST_MODE: print(f"<<< _on_dci_setting_change (stored={self._dci_settings})")

	def _translate_dci_settings(self, settings: DciSettings) -> DciSettings:
		return DciSettings(
			range_mode=self._translator.translate("range_mode", settings.range_mode),
			range_val=self._translator.translate("dci_range", settings.range_val),
			resolution=self._translator.translate_resolution(
				settings.resolution,
				gui_values.DCI_RESOLUTION_DIGITS[1],
				self._translator.translate("dci_max_resolution", settings.range_val),
			),
			aperture_mode=self._translator.translate("aperture_mode", settings.aperture_mode),
			time=settings.time,
		)

	def _on_dcv_start(self):
		if self.TEST_MODE: print(">>> _on_dcv_start")
		try:
			requested_settings = self._translate_dcv_settings(self._view.get_dcv_settings())
			if self.TEST_MODE: print(f"    SEND_TO_INSTRUMENT: {requested_settings}")
			actual_settings = self._instr_ctrl.set_dcv(requested_settings)
			if self.TEST_MODE: print(f"    RECEIVED_FROM_INSTRUMENT: {actual_settings}")
			self._dcv_settings = self._translate_dcv_settings_to_gui(actual_settings)
			self._show_dcv_settings()
			self._view.set_status("DCV configured.")
		except Exception as error:
			self._view.set_status(f"DCV start error: {error}")
			if self.TEST_MODE: print(f"<<< _on_dcv_start (error={error})")
			return
		# GUI labels hold non-ASCII units (Ω): not printed, a cp1252 console would raise
		if self.TEST_MODE: print("<<< _on_dcv_start")

	def _show_dcv_settings(self):
		"""Show the applied DCV settings (GUI format), PLC included when known."""
		self._view.set_dcv_settings(self._dcv_settings)
		if self._line_frequency is not None:
			self._view.set_aperture_values(
				"DCV",
				self._dcv_settings.time,
				self.calculate_plc(self._dcv_settings.time),
			)

	def _on_dci_start(self):
		if self.TEST_MODE: print(">>> _on_dci_start")
		try:
			requested_settings = self._translate_dci_settings(self._view.get_dci_settings())
			actual_settings = self._instr_ctrl.set_dci(requested_settings)
			self._dci_settings = actual_settings
			self._view._on_dci_settings_received(
				self._translate_dci_settings_to_gui(actual_settings)
			)
			self._view.set_status("DCI measurement started.")
		except Exception as error:
			self._view.set_status(f"DCI start error: {error}")
			if self.TEST_MODE: print(f"<<< _on_dci_start (error={error})")
			return
		if self.TEST_MODE: print(f"<<< _on_dci_start (settings={self._dci_settings})")

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

	def _on_ohms_setting_change(self, settings: OhmsSettings):
		if self.TEST_MODE: print(f">>> _on_ohms_setting_change (range_val={settings.range_val}, mode={settings.mode}, resolution={settings.resolution})")
		translated_settings = OhmsSettings(
			four=False,
			range_val=self._translator.translate("ohm_range", settings.range_val),
			resolution=settings.resolution,
			mode= settings.mode,
			filter=settings.filter,
			low_i=settings.low_i,
			aperture_mode=self._translator.translate("aperture_mode", settings.aperture_mode),
			time=settings.time
		)
		if self.TEST_MODE: print(f"    TRANSLATED: range_val={translated_settings.range_val}, mode={translated_settings.mode}")
		self._ohms_settings = translated_settings
		if self.TEST_MODE: print(f"<<< _on_ohms_setting_change (stored={self._ohms_settings})")

	def _on_continuous_start(self):
		if self.TEST_MODE: print(f">>> _on_continuous_start")
		if self._reading_thread is not None:
			if self.TEST_MODE: print(f"<<< _on_continuous_start (thread already running)")
			return
		self._reading_thread=ReadingThread(self._instr_ctrl)
		self._reading_thread.reading_ready.connect(self._view.set_read) #emits from measurment_controller are redirected to view
		self._reading_thread.start()
		self._view.start_button.setEnabled(False)
		self._view.stop_button.setEnabled(True)
		self._view.set_status("Continuous reading started.")
		if self.TEST_MODE: print(f"<<< _on_continuous_start")
		

	def _on_continuous_stop(self):
		if self.TEST_MODE: print(f">>> _on_continuous_stop")
		if self._reading_thread is None:
			if self.TEST_MODE: print(f"<<< _on_continuous_stop (no thread running)")
			return True
		self._reading_thread.stop()
		self._reading_thread = None
		self._view.set_status("Stopped.")
		self._view.stop_button.setEnabled(False)
		self._view.start_button.setEnabled(True)
		if self.TEST_MODE: print(f"<<< _on_continuous_stop")

	def _on_scan(self):
		if self.TEST_MODE: print(">>> _on_scan")
		try:
			resources = self._instr_ctrl.scan_resources()
			self._view.set_scan_results(resources)
			self._view.set_status(f"Found {len(resources)} VISA resource(s)")
			if self.TEST_MODE: print(f"    VISA_RESOURCES: {resources}")
		except Exception as error:
			self._view.set_scan_results([])
			self._view.set_status(f"Scan error: {error}")
			if self.TEST_MODE: print(f"    SCAN_ERROR: {error}")
		if self.TEST_MODE: print("<<< _on_scan")

	def _on_connect(self, address: str):
		if self.TEST_MODE: print(f">>> _on_connect (address={address})")
		try:
			self._instr_ctrl.connect(address)
			# Line frequency is read once per connection; the NPLC limits derive from it
			self._line_frequency = self._instr_ctrl.get_line_frequency()
			min_time = scpi.NPLC_MIN / self._line_frequency
			max_time = scpi.APERTURE_TIME_MAX
			min_nplc = scpi.NPLC_MIN
			max_nplc = scpi.APERTURE_TIME_MAX * self._line_frequency
			self._view.set_aperture_ranges(min_time, max_time, min_nplc, max_nplc)
			# The connection resets the instrument (*RST), back to the defaults
			self._dcv_settings = defaults.dcv_settings()
			self._view.set_dcv_settings(self._dcv_settings)
			self._update_view_aperture_values()
			self._view.set_connected()
			self._view.set_status(f"Connected to {address}")
			if self.TEST_MODE: print(f"<<< _on_connect (connected={address})")
		except Exception as error:
			self._view.set_status(f"Connection error: {error}")
			if self.TEST_MODE: print(f"<<< _on_connect (error={error})")

	def _on_disconnect(self):
		if self.TEST_MODE: print(">>> _on_disconnect")
		if not self._instr_ctrl.is_connected():
			self._view.set_disconnected()
			return

		try:
			self._instr_ctrl.disconnect()
			self._line_frequency = None
			self._view.set_disconnected()
			self._view.set_status("Disconnected")
			if self.TEST_MODE: print("<<< _on_disconnect")
		except Exception as error:
			self._view.set_status(f"Disconnect error: {error}")
			if self.TEST_MODE: print(f"<<< _on_disconnect (error={error})")