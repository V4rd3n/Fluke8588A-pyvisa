from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMainWindow
import os, json
from Fluke8588A.data.spin_box_values import (
	AC_COUNTGATE,
	AC_PK2PK,
	AC_SECREAD,
	ACV_COUPIMP,
	ACV_RANGE,
	I_RANGE,
	RMS_FILTER,
	get_ac_digit_val,
	get_dci_range,
	get_dc_digit_val,
	get_digi_i_coupling_impedance,
	get_digi_i_range,
	get_digi_v_coupling_impedance,
	get_digi_v_range,
	get_dcv_impedence,
	get_dcv_range,
	get_functions,
	get_max_nplc,
	get_max_time,
	get_min_nplc,
	get_min_time,
	get_ohm_modes,
	get_ohm_range,
	get_ohm_tru_range,
)
from Fluke8588A.instrument.config import InstrumentConfig
import Fluke8588A.instrument.config as config 
from Fluke8588A.data.settings import AciSettings, AcvSettings, DciSettings, DcvSettings, OhmsSettings
from Fluke8588A.views.plot_widget import DmmPlotWidget
main_window_loc = os.path.join(os.path.dirname(__file__), "..", "new_ui", "main_window.ui")
class MainWindow(QMainWindow):
	scan_requested = pyqtSignal()
	connect_requested = pyqtSignal(str)
	disconnect_requested = pyqtSignal()
	dcv_start_requested = pyqtSignal()
	dci_start_requested = pyqtSignal()
	trigger_base_requested = pyqtSignal()
	aperture_value_changed = pyqtSignal(str, str, float)

	""" init_requested = pyqtSignal()
	mode_changed = pyqtSignal()
	read_requested = pyqtSignal()
	set_requested = pyqtSignal()
	measurment_setup_requested = pyqtSignal()
	trigger_requested = pyqtSignal()
	dcv_signal = pyqtSignal(DcvSettings)
	dci_signal = pyqtSignal(DciSettings)
	ohms_signal = pyqtSignal(OhmsSettings)
	continuous_start_requested = pyqtSignal()
	continuous_stop_requested  = pyqtSignal()
	append_value = pyqtSignal(float)	 """

	def __init__(self):
		super().__init__()
		uic.loadUi(main_window_loc, self)
		self._connected = False
		# self.set_mode_visible(self.current_mode)
		self._connect_signals()
		self._init_widgets()
		
	def _connect_signals(self):
		self.scan_pushbutton.pressed.connect(self.scan_requested)
		self.connect_pushbutton.pressed.connect(self._on_connect_pressed)
		self.funcopen_pushbutton.clicked.connect(
			lambda: self._on_function_selected(self.op_combobox.currentText())
		)
		self.digi_tens_radiobutton.toggled.connect(self._update_digitize_controls)
		self.digi_curr_radiobutton.toggled.connect(self._update_digitize_controls)
		self.ohms_mode_combobox.currentTextChanged.connect(self._update_ohms_controls)
		self.dcv_start_pushbutton.pressed.connect(self.dcv_start_requested)
		self.dci_start_pushbutton.pressed.connect(self.dci_start_requested)
		self.trig_base_pushbutton.pressed.connect(self.trigger_base_requested)
		for function, time_spinbox, plc_spinbox in (
			("DCV", self.dcv_time_spinbox, self.dcv_plc_spinbox),
			("DCI", self.dci_time_spinbox, self.dci_plc_spinbox),
			("OHMS", self.ohms_time_radiobutton, self.ohms_plc_radiobutton),
		):
			time_spinbox.valueChanged.connect(
				lambda value, function=function: self.aperture_value_changed.emit(function, "time", value)
			)
			plc_spinbox.valueChanged.connect(
				lambda value, function=function: self.aperture_value_changed.emit(function, "plc", value)
			)
		for function, manual_radiobutton in (
			("DCV", self.dcv_man_radiobutton),
			("DCI", self.dci_man_radiobutton),
			("OHMS", self.ohms_man_radiobutton),
		):
			manual_radiobutton.toggled.connect(
				lambda checked, function=function: self._set_aperture_controls_enabled(function, checked)
			)
		self.acv_couimp_combobox.currentTextChanged.connect(
			self._update_acv_path_controls
		)
		self.acv_secread_combobox.currentTextChanged.connect(
			self._update_acv_peak_to_peak_control
		)
		self.aci_sac_radiobutton.toggled.connect(
			self._update_aci_path_controls
		)
		self.aci_secread_combobox.currentTextChanged.connect(
			self._update_aci_peak_to_peak_control
		)
		""" #init set mode
		self.init_button.pressed.connect(self.init_requested)
		self.mode_combo.currentTextChanged.connect(self.mode_changed)
		self.set_button.pressed.connect(self.set_requested) 
		#dcv signals
		self.dcv_range_combo.currentTextChanged.connect(self._on_dcv_changed)
		self.dcv_res_spin.valueChanged.connect(self._on_dcv_changed)
		self.dcv_zin_combo.currentTextChanged.connect(self._on_dcv_changed)
		self.dcv_measure_setup_button.pressed.connect(self.measurment_setup_requested) #to be
		#dci signals
		self.dci_range_combo.currentTextChanged.connect(self._on_dci_changed)
		self.dci_res_spin.valueChanged.connect(self._on_dci_changed)
		self.dci_measure_setup_button.pressed.connect(self.measurment_setup_requested) #to be
		#ohms signals
		self.ohm_range_combo.currentTextChanged.connect(self._on_ohms_changed)
		self.ohm_res_spin.valueChanged.connect(self._on_ohms_changed)
		self.ohm_mode_combo.currentTextChanged.connect(self._on_ohms_changed)
		self.ohm_filter_check.stateChanged.connect(self._on_ohms_changed)
		self.ohm_lowi_check.stateChanged.connect(self._on_ohms_changed)
		self.ohm_measure_setup.pressed.connect(self.measurment_setup_requested) #to be
		#reading 
		self.read_button.pressed.connect(self.read_requested)
		self.start_button.pressed.connect(self.continuous_start_requested)
		self.stop_button.pressed.connect(self.continuous_stop_requested)
		#trigger
		self.trigger_button.pressed.connect(self.trigger_requested) #to be """
		 

	def _init_widgets(self):
		self._init_interactions()
		self.op_combobox.addItems(get_functions())
		self.dcv_range_combobox.addItems(get_dcv_range())
		self.dcv_imp_combobox.addItems(get_dcv_impedence())
		self.dcv_resol_spinbox.setRange(min(get_dc_digit_val()), max(get_dc_digit_val()))
		self.dci_range_combobox.addItems(get_dci_range())
		self.dci_resol_spinbox.setRange(min(get_dc_digit_val()), max(get_dc_digit_val()))
		self.acv_range_combobox.addItems(ACV_RANGE)
		self.acv_resol_spinbox.setRange(min(get_ac_digit_val()), max(get_ac_digit_val()))
		self.acv_filter_combobox.addItems(RMS_FILTER)
		self.acv_couimp_combobox.addItems(ACV_COUPIMP)
		self.acv_secread_combobox.addItems(AC_SECREAD)
		self.acv_count_combobox.addItems(AC_COUNTGATE)
		self.acv_pktpk_combobox.addItems(AC_PK2PK)
		self.aci_range_combobox.addItems(I_RANGE)
		self.aci_resol_spinbox.setRange(min(get_ac_digit_val()), max(get_ac_digit_val()))
		self.aci_filter_combobox.addItems(RMS_FILTER)
		self.aci_secread_combobox.addItems(AC_SECREAD)
		self.aci_count_combobox.addItems(AC_COUNTGATE)
		self.aci_pktpk_combobox.addItems(AC_PK2PK)
		self.ohms_range_combobox.addItems(get_ohm_range())
		self.ohms_resol_spinbox.setRange(min(get_dc_digit_val()), max(get_dc_digit_val()))
		self.ohms_mode_combobox.addItems(get_ohm_modes())
		self._update_ohms_controls(self.ohms_mode_combobox.currentText())
		self.digi_tens_radiobutton.setChecked(True)
		self._update_digitize_controls(self.digi_tens_radiobutton.isChecked())
		for time_spinbox, plc_spinbox in (
			(self.dcv_time_spinbox, self.dcv_plc_spinbox),
			(self.dci_time_spinbox, self.dci_plc_spinbox),
			(self.ohms_time_radiobutton, self.ohms_plc_radiobutton),
		):
			time_spinbox.setRange(get_min_time(), get_max_time())
			time_spinbox.setDecimals(4)
			plc_spinbox.setRange(get_min_nplc(), get_max_nplc())
			plc_spinbox.setDecimals(3)
		self._set_aperture_controls_enabled("DCV", self.dcv_man_radiobutton.isChecked())
		self._set_aperture_controls_enabled("DCI", self.dci_man_radiobutton.isChecked())
		self._set_aperture_controls_enabled("OHMS", self.ohms_man_radiobutton.isChecked())
		self._update_acv_path_controls(self.acv_couimp_combobox.currentText())
		self._update_acv_peak_to_peak_control(self.acv_secread_combobox.currentText())
		self._update_aci_path_controls(self.aci_sac_radiobutton.isChecked())
		self._update_aci_peak_to_peak_control(self.aci_secread_combobox.currentText())
		""" self.gpib_addr_spin.setRange(0, 30)
		self.gpib_addr_spin.setValue(InstrumentConfig.DEFAULT_ADDRESS)
		self.mode_combo.addItems(get_functions())
		#dcv
		self.dcv_range_combo.addItems(get_dcv_range())
		self.dcv_zin_combo.addItems(get_dcv_impedence())
		self.dcv_res_spin.setRange(min(get_dc_digit_val()), max(get_dc_digit_val()))
		#dci
		self.dci_range_combo.addItems(get_dci_range())
		self.dci_res_spin.setRange(min(get_dc_digit_val()), max(get_dc_digit_val()))
		#ohms
		self.ohm_range_combo.addItems(get_ohm_range())
		self.ohm_res_spin.setRange(min(get_dc_digit_val()), max(get_dc_digit_val()))
		self.ohm_mode_combo.addItems(get_ohm_modes()) 
		
		#reading
		self.stop_button.setEnabled(False)
		self.start_button.setEnabled(False)
		#plotting - connect signal to plot widget
		self.plot_widget._connect_signals(self) """

	def _init_interactions(self):
		# Tab hiding part, we iterate the tabs index and show them only if == settings_index,
		# practically true only with the settings tab, we hide all but it
		settings_index = self.tabWidget.indexOf(self.setting_tab)

		for index in range(self.tabWidget.count()):
			self.tabWidget.setTabVisible(index, index == settings_index)

		# active tab at launch is settings 
		self.tabWidget.setCurrentIndex(settings_index)

		# Disable groups and objects still not useful
		self.func_groupbox.setEnabled(False)
		self.trig_groupbox.setEnabled(False)
		self.scan_combobox.setEnabled(False)
		self.connect_pushbutton.setEnabled(False)

	def _on_function_selected(self, function: str):
		function_tabs = {
			"DCV": self.dcv_tab,
			"ACV": self.acv_tab,
			"DCI": self.dci_tab,
			"ACI": self.aci_tab,
			"OHMS": self.ohms_tab,
			"DIGITIZE": self.digi_tab,
		}
		selected_tab = function_tabs.get(function)
		if selected_tab is None:
			return

		settings_index = self.tabWidget.indexOf(self.setting_tab)
		selected_index = self.tabWidget.indexOf(selected_tab)
		for index in range(self.tabWidget.count()):
			self.tabWidget.setTabVisible(index, index in (settings_index, selected_index))
		self.tabWidget.setCurrentIndex(selected_index)

	def set_scan_results(self, resources: list[dict[str, str]]):
		self.scan_combobox.clear()
		for resource in resources:
			self.scan_combobox.addItem(
				resource["display_name"],
				userData=resource,
			)
	
		resources_found = bool(resources)
		self.scan_combobox.setEnabled(resources_found)
		self.connect_pushbutton.setEnabled(resources_found)

	def _on_connect_pressed(self):
		if self._connected:
			self.disconnect_requested.emit()
			return

		resource = self.scan_combobox.currentData()
		if resource is not None:
			self.connect_requested.emit(resource["address"])

	def set_connected(self):
		self._connected = True
		self.scan_pushbutton.setEnabled(False)
		self.scan_combobox.setEnabled(False)
		self.connect_pushbutton.setEnabled(True)
		self.connect_pushbutton.setText("Disconnect")
		self.func_groupbox.setEnabled(True)
		self.trig_groupbox.setEnabled(True)

	def set_disconnected(self):
		self._connected = False
		self.scan_pushbutton.setEnabled(True)
		self.scan_combobox.setEnabled(self.scan_combobox.count() > 0)
		self.connect_pushbutton.setEnabled(self.scan_combobox.count() > 0)
		self.connect_pushbutton.setText("Connect")
		self.func_groupbox.setEnabled(False)
		self.trig_groupbox.setEnabled(False)

	def set_status(self, status: str):
		self.statusbar.showMessage(status, 7000)

	def get_dcv_settings(self) -> DcvSettings:
		return DcvSettings(
			range_mode="AUTO" if self.dcv_range_combobox.currentText() == "AUTO" else "MAN",
			range_val=self.dcv_range_combobox.currentText(),
			resolution=self.dcv_resol_spinbox.value(),
			zin=self.dcv_imp_combobox.currentText(),
			aperture_mode=self._get_aperture_mode(
				self.dcv_auto_radiobutton,
				self.dcv_autofast_radiobutton,
			),
			time=self.dcv_time_spinbox.value(),
		)

	def get_dci_settings(self) -> DciSettings:
		return DciSettings(
			range_mode="AUTO" if self.dci_range_combobox.currentText() == "AUTO" else "MAN",
			range_val=self.dci_range_combobox.currentText(),
			resolution=self.dci_resol_spinbox.value(),
			aperture_mode=self._get_aperture_mode(
				self.dci_auto_radiobutton,
				self.dci_autofast_radiobutton,
			),
			time=self.dci_time_spinbox.value(),
		)

	def _get_aperture_mode(self, auto_radiobutton, autofast_radiobutton) -> str:
		if auto_radiobutton.isChecked():
			return "AUTO"
		if autofast_radiobutton.isChecked():
			return "FAST"
		return "MAN"
		
	""" @property
	def current_gpib_address(self)->int:
		return self.gpib_addr_spin.value() """

	""" @property
	def current_mode(self)->str:
		return self.mode_combo.currentText()


	@property
	def current_dcv_range(self)->str:
		return self.dcv_range_combo.currentText()

	@property
	def current_dcv_resolution(self)->int:
		return self.dcv_res_spin.value()

	@property
	def current_dcv_measurement_mode(self)->str:
		return self.dcv_measure_setup_button.currentText()

	@property
	def current_dcv_zin(self)->str:
		return self.dcv_zin_combo.currentText()

	@property
	def current_time(self)->float:
		return float(self.dcv_time_label.currentText())
	
	@property
	def current_nplc(self)->float:
		return float(self.dcv_nplc_label.currentText())
	
	@property
	def current_ohm_range(self)->str:
		return self.ohm_range_combo.currentText()

	@property
	def current_ohm_resolution(self)->int:
		return self.ohm_res_spin.value()

	@property
	def current_ohm_mode(self)->str:
		return self.ohm_mode_combo.currentText()

	
	def set_disconnected(self):
		self.init_button.setEnabled(True)
		self.read_button.setEnabled(False)
		self.mode_combo.setEnabled(False)
		self.set_button.setEnabled(False)
		self.start_button.setEnabled(False)	
		self.stop_button.setEnabled(False)

		#add function that hides all widgets etc

	def set_connected(self):	
		self.init_button.setEnabled(True)
		self.read_button.setEnabled(True)
		self.mode_combo.setEnabled(True)
		self.set_button.setEnabled(True)
		self.start_button.setEnabled(True)	
		self.stop_button.setEnabled(False)
		#add fucntion that shows current mode widgets


	def _save_to_json(self):
		settings = {
			"dcv": {
				"range_mode": "AUTO" if self.dcv_range_combo.currentText() == "AUTO" else "MAN",
				"range_val": self.dcv_range_combo.currentText(),
				"resolution": self.dcv_res_spin.value(),
				"zin": self.dcv_zin_combo.currentText(),
				"aperture_mode": self.dcv_measure_setup_button.text(),
				"time": self.dcv_time_label.text()
			},
			"dci": {
				"range_mode": "AUTO" if self.dci_range_combo.currentText() == "AUTO" else "MAN",
				"range_val": self.dci_range_combo.currentText(),
				"resolution": self.dci_res_spin.value(),
				"aperture_mode": self.dci_measure_setup_button.text(),
				"time": self.dci_time_label.text()
			},
			# "acv": {
			# 	pass
			# },
			# "aci": {
			# 	pass
			# },	
			"ohms": {
				"four": True, #viewer doesnt hanle logic, so it just sets to true
				"range_val": self.ohm_range_combo.currentText(),
				"resolution": self.ohm_res_spin.value(),
				"mode": self.ohm_mode_combo.currentText(),
				"filter": self.ohm_filter_check.isChecked(),
				"low_i": self.ohm_lowi_check.isChecked(),
				"aperture_mode": self.ohm_measure_setup.text(),
				"time": self.ohm_time_label.text()
			},
		}
		with open(config.JSON_GUI_FILE_NAME, "w") as f:
			json.dump(settings, f)	
		
	def set_read(self, value: int):
		self.measure_display_label.setText(str(value))
		self.append_value.emit(float(value))
	
	def set_mode_visible(self, mode: str):
		self.dcv_widget.setVisible(mode == "DCV")
		self.dci_widget.setVisible(mode=="DCI")
		self.ohm_widget.setVisible(mode == "OHMS")
		# self.acv_widget.setVisible(mode == "ACV")
		# self.aci_widget.setVisible(mode == "ACI")

	def set_status(self, status: str):
		self.status_label.setText(status)

	def set_aperture_mode(self, mode: str):
		self.dcv_measure_setup_button.setText(mode)
		self.dci_measure_setup_button.setText(mode)
		self.ohm_measure_setup.setText(mode)

	def set_time_value(self, time: float):
		self.dcv_time_label.setText(str(time))
		self.dci_time_label.setText(str(time))
		self.ohm_time_label.setText(str(time))

	def set_nplc_value(self, nplc: float):
		self.dcv_nplc_label.setText(str(nplc))
		self.dci_nplc_label.setText(str(nplc))
		self.ohm_nplc_label.setText(str(nplc))

	def _on_dcv_changed(self):
		self.dcv_signal.emit(DcvSettings(
			range_mode = "AUTO" if self.dcv_range_combo.currentText() == "AUTO" else "MAN",
			range_val = self.dcv_range_combo.currentText(),
			resolution = self.dcv_res_spin.value(),
			zin = self.dcv_zin_combo.currentText(),
			aperture_mode= self.dcv_measure_setup_button.text(),
			time = self.dcv_time_label.text()
    		)
		)
		
	def _on_dci_changed(self):
		self.dci_signal.emit(DciSettings(
			range_mode = "AUTO" if self.dci_range_combo.currentText() == "AUTO" else "MAN",
			range_val = self.dci_range_combo.currentText(),
			resolution = self.dci_res_spin.value(),
			aperture_mode = self.dci_measure_setup_button.text(),
			time = self.dci_time_label.text()
		)
	)
	
	def _on_ohms_changed(self):
		self.ohms_signal.emit(OhmsSettings(
			four = True, #viewer doesnt hanle logic, so it just sets to true
			range_val = self.ohm_range_combo.currentText(),
			resolution = self.ohm_res_spin.value(),
			mode = self.ohm_mode_combo.currentText(),
			filter = self.ohm_filter_check.isChecked(),
			low_i = self.ohm_lowi_check.isChecked(),
			aperture_mode = self.ohm_measure_setup.text(),
			time = self.ohm_time_label.text()
		)
	)
	"""

	def set_aperture_values(self, function: str, time: float, plc: float):
		spinboxes = {
			"DCV": (self.dcv_time_spinbox, self.dcv_plc_spinbox),
			"DCI": (self.dci_time_spinbox, self.dci_plc_spinbox),
			"OHMS": (self.ohms_time_radiobutton, self.ohms_plc_radiobutton),
		}
		time_spinbox, plc_spinbox = spinboxes[function]
		time_spinbox.blockSignals(True)
		plc_spinbox.blockSignals(True)
		time_spinbox.setValue(time)
		plc_spinbox.setValue(plc)
		time_spinbox.blockSignals(False)
		plc_spinbox.blockSignals(False)

	def _set_aperture_controls_enabled(self, function: str, enabled: bool):
		spinboxes = {
			"DCV": (self.dcv_time_spinbox, self.dcv_plc_spinbox),
			"DCI": (self.dci_time_spinbox, self.dci_plc_spinbox),
			"OHMS": (self.ohms_time_radiobutton, self.ohms_plc_radiobutton),
		}
		for spinbox in spinboxes[function]:
			spinbox.setEnabled(enabled)

	def _update_digitize_controls(self, voltage_selected: bool):
		if voltage_selected != self.digi_tens_radiobutton.isChecked():
			return

		range_values = get_digi_v_range() if voltage_selected else get_digi_i_range()
		coupling_values = (
			get_digi_v_coupling_impedance()
			if voltage_selected
			else get_digi_i_coupling_impedance()
		)
		self._replace_combo_items(self.digi_range_combobox, range_values)
		self._replace_combo_items(self.digi_coupimp_combobox, coupling_values)

	def _update_ohms_controls(self, mode: str):
		range_values = get_ohm_tru_range() if mode == "4W Tru" else get_ohm_range()
		self._replace_combo_items(self.ohms_range_combobox, range_values)

		filter_enabled = mode != "4W Tru"
		self.ohms_filoff_radiobutton.setEnabled(filter_enabled)
		self.ohms_fillon_radiobutton.setEnabled(filter_enabled)
		if not filter_enabled:
			self.ohms_filoff_radiobutton.setChecked(True)

	def _replace_combo_items(self, combo_box, values: list[str]):
		current_value = combo_box.currentText()
		combo_box.blockSignals(True)
		combo_box.clear()
		combo_box.addItems(values)
		combo_box.setCurrentText(current_value if current_value in values else values[0])
		combo_box.blockSignals(False)

	def _update_acv_path_controls(self, coupling: str):
		signal_path_is_ac = coupling.startswith("AC")
		self.acv_ac_radiobutton.setChecked(signal_path_is_ac)
		self.acv_dc_radiobutton.setChecked(not signal_path_is_ac)
		self.acv_ac_radiobutton.setEnabled(not signal_path_is_ac)
		self.acv_dc_radiobutton.setEnabled(not signal_path_is_ac)

	def _update_aci_path_controls(self, signal_path_is_ac: bool):
		self.aci_fac_radiobutton.setChecked(signal_path_is_ac)
		self.aci_fdc_radiobutton.setChecked(not signal_path_is_ac)
		self.aci_fac_radiobutton.setEnabled(not signal_path_is_ac)
		self.aci_fdc_radiobutton.setEnabled(not signal_path_is_ac)

	def _update_acv_peak_to_peak_control(self, secondary_reading: str):
		self.acv_pktpk_combobox.setEnabled(secondary_reading == "Pk to Pk")

	def _update_aci_peak_to_peak_control(self, secondary_reading: str):
		self.aci_pktpk_combobox.setEnabled(secondary_reading == "Pk to Pk")

	def _on_dcv_settings_received(self, settings: DcvSettings):
		self.dcv_range_combobox.setCurrentText(settings.range_val)
		self.dcv_resol_spinbox.setValue(settings.resolution)
		self.dcv_imp_combobox.setCurrentText(settings.zin)
		self.dcv_man_radiobutton.setChecked(settings.aperture_mode == "MAN")
		self.dcv_autofast_radiobutton.setChecked(settings.aperture_mode == "FAST")
		self.dcv_auto_radiobutton.setChecked(settings.aperture_mode == "AUTO")
		self.dcv_time_spinbox.setValue(settings.time)

	def _on_dci_settings_received(self, settings: DciSettings):
		self.dci_range_combobox.setCurrentText(settings.range_val)
		self.dci_resol_spinbox.setValue(settings.resolution)
		self.dci_man_radiobutton.setChecked(settings.aperture_mode == "MAN")
		self.dci_autofast_radiobutton.setChecked(settings.aperture_mode == "FAST")
		self.dci_auto_radiobutton.setChecked(settings.aperture_mode == "AUTO")
		self.dci_time_spinbox.setValue(settings.time)

	def _on_acv_settings_received(self, settings: AcvSettings):
		self.acv_range_combobox.setCurrentText(settings.range_val)
		self.acv_resol_spinbox.setValue(settings.resolution)
		self.acv_filter_combobox.setCurrentText(settings.rms_filter)
		self.acv_couimp_combobox.setCurrentText(settings.coupling_impedance)
		self.acv_secread_combobox.setCurrentText(settings.secondary_reading)
		self.acv_ac_radiobutton.setChecked(settings.frequency_path_coupling == "AC")
		self.acv_dc_radiobutton.setChecked(settings.frequency_path_coupling == "DC")
		self.acv_off_radiobutton.setChecked(settings.frequency_path_bandwidth_limit == "OFF")
		self.acv_on_radiobutton.setChecked(settings.frequency_path_bandwidth_limit == "ON")
		self.acv_count_combobox.setCurrentText(settings.counter_gate)
		self.acv_wide_radiobutton.setChecked(settings.bandwidth == "Wideband")
		self.acv_ext_radiobutton.setChecked(settings.bandwidth == "Extended HF")
		self.acv_pktpk_combobox.setCurrentText(settings.peak_to_peak)
		self._update_acv_path_controls(settings.coupling_impedance)
		self._update_acv_peak_to_peak_control(settings.secondary_reading)

	def _on_aci_settings_received(self, settings: AciSettings):
		self.aci_range_combobox.setCurrentText(settings.range_val)
		self.aci_resol_spinbox.setValue(settings.resolution)
		self.aci_filter_combobox.setCurrentText(settings.rms_filter)
		self.aci_sac_radiobutton.setChecked(settings.signal_path_coupling == "AC")
		self.aci_sdc_radiobutton.setChecked(settings.signal_path_coupling == "DC")
		self.aci_secread_combobox.setCurrentText(settings.secondary_reading)
		self.aci_fac_radiobutton.setChecked(settings.frequency_path_coupling == "AC")
		self.aci_fdc_radiobutton.setChecked(settings.frequency_path_coupling == "DC")
		self.aci_off_radiobutton.setChecked(settings.frequency_path_bandwidth_limit == "OFF")
		self.aci_on_radiobutton.setChecked(settings.frequency_path_bandwidth_limit == "ON")
		self.aci_count_combobox.setCurrentText(settings.counter_gate)
		self.aci_pktpk_combobox.setCurrentText(settings.peak_to_peak)
		self._update_aci_path_controls(settings.signal_path_coupling == "AC")
		self._update_aci_peak_to_peak_control(settings.secondary_reading)

	def _on_ohms_settings_received(self, settings: OhmsSettings):
		self.ohms_range_combobox.setCurrentText(settings.range_val)
		self.ohms_resol_spinbox.setValue(settings.resolution)
		self.ohms_mode_combobox.setCurrentText(settings.mode)
		self.ohms_lolon_radiobutton.setChecked(False)
		self.ohms_loloff_radiobutton.setChecked(True)
		self.ohms_man_radiobutton.setChecked(settings.aperture_mode == "MAN")
		self.ohms_autofast_radiobutton.setChecked(settings.aperture_mode == "FAST")
		self.ohms_auto_radiobutton.setChecked(settings.aperture_mode == "AUTO")
		self.ohms_time_radiobutton.setValue(settings.time)
		self.ohms_fillon_radiobutton.setChecked(settings.filter)
		self.ohms_filoff_radiobutton.setChecked(not settings.filter)