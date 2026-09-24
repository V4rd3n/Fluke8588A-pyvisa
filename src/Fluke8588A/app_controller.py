from src.Fluke8588A.instrument_controller import InstrumentController as InstrumentController 
from src.Fluke8588A.main_window import MainWindow  
from src.Fluke8588A.dc_measurment_setup import DcMeasurmentWindow
from src.Fluke8588A.trigger_setup import TriggerWindow
from src.Fluke8588A.data.settings import DcvSettings, DciSettings, OhmsSettings, TriggerBaseSettings
from src.Fluke8588A.measurment_controller import ReadingThread
from src.Fluke8588A.translator import Translator
import src.Fluke8588A.config as config, json
class AppController:
	TEST_MODE = True  # Set to False to disable debug output
	
	def __init__(self):
		self._view = MainWindow()
		self._meas_pop_up = DcMeasurmentWindow()
		# self._trigger_pop_up = TriggerWindow()
		self._view.set_disconnected()
		# Initialize settings objects with default values
		self._dcv_settings = DcvSettings(
			range_mode="MAN",
			range_val="1 V",
			resolution=4,
			zin="Auto",
			aperture_mode="MAN",
			time=0.1
		)
		self._dci_settings = DciSettings(
			range_mode="MAN",
			range_val="1 A",
			resolution=4,
			aperture_mode="AUTO",
			time=0.1
		)
		self._ohms_settings = OhmsSettings(
			four=False,
			range_val="1 kΩ",
			resolution=4,
			mode="2W NORMAL",
			filter=False,
			low_i=False,
			aperture_mode="AUTO",
			time=0.1
		)
		self._trigger_base_settings = TriggerBaseSettings(
			source="IMMediate",
			count=1,
			delay=0.0,
			delay_auto=True,
			holdoff=0.0,
			holdoff_auto=True,
			timer=None,
			ext_edge=None
		)
		
		self._connect_signals()
		self._view.show()
		self._instr_ctrl=InstrumentController()
		self._reading_thread= None
		self._translator = Translator()
		self._pre_translate_defaults()

	def _pre_translate_defaults(self):
		"""Translate default GUI settings to machine format upon initialization."""
		if self.TEST_MODE: print(">>> _pre_translate_defaults")
		self._on_dcv_setting_change(self._dcv_settings)
		self._on_dci_setting_change(self._dci_settings)
		self._on_ohms_setting_change(self._ohms_settings)
		if self.TEST_MODE: print("<<< _pre_translate_defaults")

	def _connect_signals(self):
		self._view.init_requested.connect(self._on_init)
		self._view.mode_changed.connect(self._on_mode_change)
		self._view.read_requested.connect(self._on_read)
		self._view.set_requested.connect(self._on_set)
		self._view.measurment_setup_requested.connect(self._on_measurment_setup_press)
		self._view.dcv_signal.connect(self._on_dcv_setting_change)
		self._view.dci_signal.connect(self._on_dci_setting_change)
		self._view.ohms_signal.connect(self._on_ohms_setting_change)
		self._meas_pop_up.mode_select.connect(self._on_aperture_mode_changed)
		self._meas_pop_up.time_select.connect(self._on_time_changed)
		self._meas_pop_up.nplc_select.connect(self._on_nplc_changed)
		self._view.continuous_start_requested.connect(self._on_continuous_start)
		self._view.continuous_stop_requested.connect(self._on_continuous_stop)

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
	
	def _translate_gui_json(self):
		with open(config.JSON_GUI_FILE_NAME, "r") as f:
			settings = json.load(f)
		translated_json = self._translate_json(settings)
		with open(config.JSON_CNTRL_FILE_NAME, "w") as f:
			json.dump(translated_json, f)

	def _translate_json(self, settings: dict) -> dict:
		"""
		Translate GUI JSON settings to machine format using mode-specific translation functions.
		
		Args:
			settings: Dictionary with measurement mode keys ('dcv', 'dci', 'ohms')
			          containing GUI format settings
			
		Returns:
			Dictionary with same structure but values translated to machine format
		"""
		translated = {}
		
		if "dcv" in settings:
			translated["dcv"] = self._translator.translate_dcv(settings["dcv"])
		
		if "dci" in settings:
			translated["dci"] = self._translator.translate_dci(settings["dci"])
		
		if "ohms" in settings:
			translated["ohms"] = self._translator.translate_ohms(settings["ohms"])
		
		return translated

	def _reverse_translate_gui_json(self):
		with open(config.JSON_CNTRL_FILE_NAME, "r") as f:
			settings = json.load(f)
		translated_json = self._reverse_translate_json(settings)
		with open(config.JSON_GUI_FILE_NAME, "w") as f:
			json.dump(translated_json, f)
	
	def _reverse_translate_json(self, settings: dict) -> dict:
		"""
		Translate CNTRL JSON settings (machine format) back to GUI format using mode-specific reverse translation functions.
		
		Args:
			settings: Dictionary with measurement mode keys ('dcv', 'dci', 'ohms')
			          containing machine format settings
			
		Returns:
			Dictionary with same structure but values translated back to GUI format
		"""
		translated = {}
		
		if "dcv" in settings:
			translated["dcv"] = self._translator.translate_dcv_reverse(settings["dcv"])
		
		if "dci" in settings:
			translated["dci"] = self._translator.translate_dci_reverse(settings["dci"])
		
		if "ohms" in settings:
			translated["ohms"] = self._translator.translate_ohms_reverse(settings["ohms"])
		
		return translated

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
				four=actual_settings.four,
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
			self._view._on_dcv_settings_received(self._dcv_settings)
		elif mode == "DCI":
			self._view._on_dci_settings_received(self._dci_settings)
		elif mode == "OHMS":
			self._view._on_ohms_settings_received(self._ohms_settings)

	def _on_measurment_setup_press(self):
		if self.TEST_MODE: print(f">>> _on_measurment_setup_press")
		self._meas_pop_up.show()
		if self.TEST_MODE: print(f"<<< _on_measurment_setup_press")

	def _on_trigger_press(self):
		if self.TEST_MODE: print(f">>> _on_trigger_press")
		self._trigger_pop_up.show()
		if self.TEST_MODE: print(f"<<< _on_trigger_press")
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

	def _set_ui_aperture_settings(self):
		self._view.set_aperture_mode()
		self._view.set_time_value()
		
	
	def _on_dcv_setting_change(self, settings: DcvSettings):
		if self.TEST_MODE: print(f">>> _on_dcv_setting_change (range_val={settings.range_val}, resolution={settings.resolution}, zin={settings.zin})")
		translated_settings = DcvSettings(
			range_mode=settings.range_mode,
			range_val = self._translator.translate("dcv_range", settings.range_val),
			resolution=settings.resolution,
			zin=self._translator.translate("impedence", settings.zin),
			aperture_mode=settings.aperture_mode,
			time=settings.time
		)
		if self.TEST_MODE: print(f"    TRANSLATED: range_val={translated_settings.range_val}, zin={translated_settings.zin}")
		self._dcv_settings = translated_settings
		if self.TEST_MODE: print(f"<<< _on_dcv_setting_change (stored={self._dcv_settings})")

	
	def _on_dci_setting_change(self, settings: DciSettings):
		if self.TEST_MODE: print(f">>> _on_dci_setting_change (range_val={settings.range_val}, resolution={settings.resolution})")
		translated_settings = DciSettings(
			range_mode=settings.range_mode,
			range_val=self._translator.translate("dci_range", settings.range_val),
			resolution=settings.resolution,
			aperture_mode=settings.aperture_mode,
			time=settings.time
		)
		if self.TEST_MODE: print(f"    TRANSLATED: range_val={translated_settings.range_val}")
		self._dci_settings = translated_settings
		if self.TEST_MODE: print(f"<<< _on_dci_setting_change (stored={self._dci_settings})")

	def _on_ohms_setting_change(self, settings: OhmsSettings):
		if self.TEST_MODE: print(f">>> _on_ohms_setting_change (range_val={settings.range_val}, mode={settings.mode}, resolution={settings.resolution})")
		translated_settings = OhmsSettings(
			four=settings.four,
			range_val=self._translator.translate("ohm_range", settings.range_val),
			resolution=settings.resolution,
			mode= settings.mode,
			filter=settings.filter,
			low_i=settings.low_i,
			aperture_mode=settings.aperture_mode,
			time=settings.time
		)
		if self.TEST_MODE: print(f"    TRANSLATED: range_val={translated_settings.range_val}, mode={translated_settings.mode}")
		self._ohms_settings = translated_settings
		if settings.mode.startswith("4W"):
			self._ohms_settings.four=True
		elif settings.mode.startswith("2W"):
			self._ohms_settings.four=False
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
