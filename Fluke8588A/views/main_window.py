from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMainWindow
import os
from Fluke8588A.data import gui_values
from Fluke8588A.data.settings import AciSettings, AcvSettings, DciSettings, DcvSettings, DigitizeSettings, OhmsSettings
# Unused: no widget of main_window.ui is a DmmPlotWidget yet
# from Fluke8588A.views.plot_widget import DmmPlotWidget
main_window_loc = os.path.join(os.path.dirname(__file__), "..", "ui", "main_window.ui")

#TODO: check ranges from manual (update settings)


class MainWindow(QMainWindow):
	scan_requested = pyqtSignal()
	connect_requested = pyqtSignal(str)
	disconnect_requested = pyqtSignal()
	dcv_set_requested = pyqtSignal()
	dci_set_requested = pyqtSignal()
	acv_set_requested = pyqtSignal()
	aci_set_requested = pyqtSignal()
	ohms_set_requested = pyqtSignal()
	digitize_set_requested = pyqtSignal()
	trigger_base_requested = pyqtSignal()
	trigger_advanced_requested = pyqtSignal()
	aperture_value_changed = pyqtSignal(str, str, float)
	closed = pyqtSignal()

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
		self.dcv_set_pushbutton.clicked.connect(self.dcv_set_requested)
		self.dci_set_pushbutton.clicked.connect(self.dci_set_requested)
		self.acv_set_pushbutton.clicked.connect(self.acv_set_requested)
		self.aci_set_pushbutton.clicked.connect(self.aci_set_requested)
		self.ohms_set_pushbutton.clicked.connect(self.ohms_set_requested)
		self.digi_set_pushbutton.clicked.connect(self.digitize_set_requested)
		self.trig_base_pushbutton.pressed.connect(self.trigger_base_requested)
		self.trig_adv_pushbutton.pressed.connect(self.trigger_advanced_requested)
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
		self.op_combobox.addItems(gui_values.FUNCTIONS)
		self.dcv_range_combobox.addItems(gui_values.DCV_RANGE)
		self.dcv_imp_combobox.addItems(gui_values.DCV_IMPEDANCE)
		self.dcv_resol_spinbox.setRange(*gui_values.DCV_RESOLUTION_DIGITS)
		self.dci_range_combobox.addItems(gui_values.I_RANGE)
		self.dci_resol_spinbox.setRange(*gui_values.DCI_RESOLUTION_DIGITS)
		self.acv_range_combobox.addItems(gui_values.ACV_RANGE)
		self.acv_resol_spinbox.setRange(*gui_values.AC_RESOLUTION_DIGITS)
		self.acv_filter_combobox.addItems(gui_values.RMS_FILTER)
		self.acv_couimp_combobox.addItems(gui_values.ACV_COUPLING_IMPEDANCE)
		self.acv_secread_combobox.addItems(gui_values.AC_SECONDARY_READING)
		self.acv_count_combobox.addItems(gui_values.AC_COUNTER_GATE)
		self.acv_pktpk_combobox.addItems(gui_values.AC_PEAK_TO_PEAK)
		self.aci_range_combobox.addItems(gui_values.I_RANGE)
		self.aci_resol_spinbox.setRange(*gui_values.AC_RESOLUTION_DIGITS)
		self.aci_filter_combobox.addItems(gui_values.RMS_FILTER)
		self.aci_secread_combobox.addItems(gui_values.AC_SECONDARY_READING)
		self.aci_count_combobox.addItems(gui_values.AC_COUNTER_GATE)
		self.aci_pktpk_combobox.addItems(gui_values.AC_PEAK_TO_PEAK)
		self.ohms_range_combobox.addItems(gui_values.OHM_RANGE)
		self.ohms_resol_spinbox.setRange(*gui_values.OHMS_RESOLUTION_DIGITS)
		self.ohms_mode_combobox.addItems(gui_values.OHM_MODES)
		self._update_ohms_controls(self.ohms_mode_combobox.currentText())
		self.digi_tens_radiobutton.setChecked(True)
		self._update_digitize_controls(self.digi_tens_radiobutton.isChecked())
		self.digi_filt_combobox.addItems(gui_values.DIGI_FILTER)
		# Decimals first: the range is rounded to the current decimals
		self.digi_aper_spinbox.setDecimals(gui_values.DIGI_APERTURE_DECIMALS)
		self.digi_aper_spinbox.setRange(*gui_values.DIGI_APERTURE_RANGE)
		self.digi_aper_spinbox.setSingleStep(gui_values.DIGI_APERTURE_STEP)
		for time_spinbox, plc_spinbox in (
			(self.dcv_time_spinbox, self.dcv_plc_spinbox),
			(self.dci_time_spinbox, self.dci_plc_spinbox),
			(self.ohms_time_radiobutton, self.ohms_plc_radiobutton),
		):
			time_spinbox.setDecimals(gui_values.APERTURE_TIME_DECIMALS)
			plc_spinbox.setDecimals(gui_values.APERTURE_PLC_DECIMALS)
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

	def closeEvent(self, event):
		# The other windows are closed by the controller, so the application quits
		self.closed.emit()
		super().closeEvent(event)

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
			range_mode=(gui_values.RANGE_MODE_AUTO if self.dcv_range_combobox.currentText() == gui_values.AUTO else gui_values.RANGE_MODE_MAN),
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
			range_mode=(gui_values.RANGE_MODE_AUTO if self.dci_range_combobox.currentText() == gui_values.AUTO else gui_values.RANGE_MODE_MAN),
			range_val=self.dci_range_combobox.currentText(),
			resolution=self.dci_resol_spinbox.value(),
			aperture_mode=self._get_aperture_mode(
				self.dci_auto_radiobutton,
				self.dci_autofast_radiobutton,
			),
			time=self.dci_time_spinbox.value(),
		)

	def get_acv_settings(self) -> AcvSettings:
		return AcvSettings(
			range_mode=(gui_values.RANGE_MODE_AUTO if self.acv_range_combobox.currentText() == gui_values.AUTO else gui_values.RANGE_MODE_MAN),
			range_val=self.acv_range_combobox.currentText(),
			resolution=self.acv_resol_spinbox.value(),
			rms_filter=self.acv_filter_combobox.currentText(),
			coupling_impedance=self.acv_couimp_combobox.currentText(),
			secondary_reading=self.acv_secread_combobox.currentText(),
			frequency_path_coupling=(
				gui_values.AC_PATH_COUPLING_AC
				if self.acv_ac_radiobutton.isChecked()
				else gui_values.AC_PATH_COUPLING_DC
			),
			frequency_path_bandwidth_limit=(
				gui_values.AC_BANDWIDTH_LIMIT_ON
				if self.acv_on_radiobutton.isChecked()
				else gui_values.AC_BANDWIDTH_LIMIT_OFF
			),
			counter_gate=self.acv_count_combobox.currentText(),
			bandwidth=(
				gui_values.ACV_BANDWIDTH_EHF
				if self.acv_ext_radiobutton.isChecked()
				else gui_values.ACV_BANDWIDTH_WIDE
			),
			peak_to_peak=self.acv_pktpk_combobox.currentText(),
		)

	def get_aci_settings(self) -> AciSettings:
		return AciSettings(
			range_mode=(gui_values.RANGE_MODE_AUTO if self.aci_range_combobox.currentText() == gui_values.AUTO else gui_values.RANGE_MODE_MAN),
			range_val=self.aci_range_combobox.currentText(),
			resolution=self.aci_resol_spinbox.value(),
			rms_filter=self.aci_filter_combobox.currentText(),
			signal_path_coupling=(
				gui_values.AC_PATH_COUPLING_AC
				if self.aci_sac_radiobutton.isChecked()
				else gui_values.AC_PATH_COUPLING_DC
			),
			secondary_reading=self.aci_secread_combobox.currentText(),
			frequency_path_coupling=(
				gui_values.AC_PATH_COUPLING_AC
				if self.aci_fac_radiobutton.isChecked()
				else gui_values.AC_PATH_COUPLING_DC
			),
			frequency_path_bandwidth_limit=(
				gui_values.AC_BANDWIDTH_LIMIT_ON
				if self.aci_on_radiobutton.isChecked()
				else gui_values.AC_BANDWIDTH_LIMIT_OFF
			),
			counter_gate=self.aci_count_combobox.currentText(),
			peak_to_peak=self.aci_pktpk_combobox.currentText(),
		)

	def get_ohms_settings(self) -> OhmsSettings:
		return OhmsSettings(
			range_mode=(gui_values.RANGE_MODE_AUTO if self.ohms_range_combobox.currentText() == gui_values.AUTO else gui_values.RANGE_MODE_MAN),
			range_val=self.ohms_range_combobox.currentText(),
			resolution=self.ohms_resol_spinbox.value(),
			mode=self.ohms_mode_combobox.currentText(),
			filter=self.ohms_fillon_radiobutton.isChecked(),
			low_current=self.ohms_lolon_radiobutton.isChecked(),
			aperture_mode=self._get_aperture_mode(
				self.ohms_auto_radiobutton,
				self.ohms_autofast_radiobutton,
			),
			time=self.ohms_time_radiobutton.value(),
		)

	def get_digitize_settings(self) -> DigitizeSettings:
		return DigitizeSettings(
			signal=(
				gui_values.DIGI_SIGNAL_VOLTAGE
				if self.digi_tens_radiobutton.isChecked()
				else gui_values.DIGI_SIGNAL_CURRENT
			),
			range_val=self.digi_range_combobox.currentText(),
			coupling_impedance=self.digi_coupimp_combobox.currentText(),
			filter=self.digi_filt_combobox.currentText(),
			aperture=self.digi_aper_spinbox.value(),
		)

	def _get_aperture_mode(self, auto_radiobutton, autofast_radiobutton) -> str:
		if auto_radiobutton.isChecked():
			return gui_values.APERTURE_AUTO
		if autofast_radiobutton.isChecked():
			return gui_values.APERTURE_FAST
		return gui_values.APERTURE_MAN
		
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

	def set_aperture_ranges(
		self,
		min_time: float,
		max_time: float,
		min_nplc: float,
		max_nplc: float,
	) -> None:
		for time_spinbox, plc_spinbox in (
			(self.dcv_time_spinbox, self.dcv_plc_spinbox),
			(self.dci_time_spinbox, self.dci_plc_spinbox),
			(self.ohms_time_radiobutton, self.ohms_plc_radiobutton),
		):
			time_spinbox.setRange(min_time, max_time)
			plc_spinbox.setRange(min_nplc, max_nplc)

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

		range_values = gui_values.DIGI_V_RANGE if voltage_selected else gui_values.DIGI_I_RANGE
		default_range = gui_values.DIGI_V_DEFAULT_RANGE if voltage_selected else gui_values.DIGI_I_DEFAULT_RANGE
		coupling_values = (
			gui_values.DIGI_V_COUPLING_IMPEDANCE
			if voltage_selected
			else gui_values.DIGI_I_COUPLING_IMPEDANCE
		)
		self._replace_combo_items(self.digi_range_combobox, range_values, default_range)
		self._replace_combo_items(
			self.digi_coupimp_combobox, coupling_values, gui_values.DIGI_DEFAULT_COUPLING_IMPEDANCE
		)

	def _update_ohms_controls(self, mode: str):
		range_values = gui_values.OHM_TRU_RANGE if mode == gui_values.OHM_MODE_4W_TRUE else gui_values.OHM_RANGE
		self._replace_combo_items(self.ohms_range_combobox, range_values)

		filter_enabled = mode != gui_values.OHM_MODE_4W_TRUE
		self.ohms_filoff_radiobutton.setEnabled(filter_enabled)
		self.ohms_fillon_radiobutton.setEnabled(filter_enabled)
		if not filter_enabled:
			self.ohms_filoff_radiobutton.setChecked(True)

	def _replace_combo_items(self, combo_box, values: list[str], default: str = None):
		# Keeps the current item if it is in values, else selects default (or the first item)
		current_value = combo_box.currentText()
		combo_box.blockSignals(True)
		combo_box.clear()
		combo_box.addItems(values)
		if current_value in values:
			combo_box.setCurrentText(current_value)
		else:
			combo_box.setCurrentText(default if default in values else values[0])
		combo_box.blockSignals(False)

	def _update_acv_path_controls(self, coupling: str):
		# An ac signal path forces the frequency path to ac; with a dc one the
		# current choice is kept, so a frequency path read back is not overwritten
		signal_path_is_ac = coupling.startswith(gui_values.AC_PATH_COUPLING_AC)
		if signal_path_is_ac:
			self.acv_ac_radiobutton.setChecked(True)
		self.acv_ac_radiobutton.setEnabled(not signal_path_is_ac)
		self.acv_dc_radiobutton.setEnabled(not signal_path_is_ac)

	def _update_aci_path_controls(self, signal_path_is_ac: bool):
		# Same as _update_acv_path_controls
		if signal_path_is_ac:
			self.aci_fac_radiobutton.setChecked(True)
		self.aci_fac_radiobutton.setEnabled(not signal_path_is_ac)
		self.aci_fdc_radiobutton.setEnabled(not signal_path_is_ac)

	def _update_acv_peak_to_peak_control(self, secondary_reading: str):
		self.acv_pktpk_combobox.setEnabled(secondary_reading == gui_values.AC_SECREAD_PK2PK)

	def _update_aci_peak_to_peak_control(self, secondary_reading: str):
		self.aci_pktpk_combobox.setEnabled(secondary_reading == gui_values.AC_SECREAD_PK2PK)

	def set_dcv_settings(self, settings: DcvSettings):
		self.dcv_range_combobox.setCurrentText(settings.range_val)
		self.dcv_resol_spinbox.setValue(settings.resolution)
		self.dcv_imp_combobox.setCurrentText(settings.zin)
		self.dcv_man_radiobutton.setChecked(settings.aperture_mode == gui_values.APERTURE_MAN)
		self.dcv_autofast_radiobutton.setChecked(settings.aperture_mode == gui_values.APERTURE_FAST)
		self.dcv_auto_radiobutton.setChecked(settings.aperture_mode == gui_values.APERTURE_AUTO)
		self.dcv_time_spinbox.setValue(settings.time)

	def set_dci_settings(self, settings: DciSettings):
		self.dci_range_combobox.setCurrentText(settings.range_val)
		self.dci_resol_spinbox.setValue(settings.resolution)
		self.dci_man_radiobutton.setChecked(settings.aperture_mode == gui_values.APERTURE_MAN)
		self.dci_autofast_radiobutton.setChecked(settings.aperture_mode == gui_values.APERTURE_FAST)
		self.dci_auto_radiobutton.setChecked(settings.aperture_mode == gui_values.APERTURE_AUTO)
		self.dci_time_spinbox.setValue(settings.time)

	def set_acv_settings(self, settings: AcvSettings):
		self.acv_range_combobox.setCurrentText(settings.range_val)
		self.acv_resol_spinbox.setValue(settings.resolution)
		self.acv_filter_combobox.setCurrentText(settings.rms_filter)
		self.acv_couimp_combobox.setCurrentText(settings.coupling_impedance)
		self.acv_secread_combobox.setCurrentText(settings.secondary_reading)
		self.acv_ac_radiobutton.setChecked(settings.frequency_path_coupling == gui_values.AC_PATH_COUPLING_AC)
		self.acv_dc_radiobutton.setChecked(settings.frequency_path_coupling == gui_values.AC_PATH_COUPLING_DC)
		self.acv_off_radiobutton.setChecked(settings.frequency_path_bandwidth_limit == gui_values.AC_BANDWIDTH_LIMIT_OFF)
		self.acv_on_radiobutton.setChecked(settings.frequency_path_bandwidth_limit == gui_values.AC_BANDWIDTH_LIMIT_ON)
		self.acv_count_combobox.setCurrentText(settings.counter_gate)
		self.acv_wide_radiobutton.setChecked(settings.bandwidth == gui_values.ACV_BANDWIDTH_WIDE)
		self.acv_ext_radiobutton.setChecked(settings.bandwidth == gui_values.ACV_BANDWIDTH_EHF)
		self.acv_pktpk_combobox.setCurrentText(settings.peak_to_peak)
		self._update_acv_path_controls(settings.coupling_impedance)
		self._update_acv_peak_to_peak_control(settings.secondary_reading)

	def set_aci_settings(self, settings: AciSettings):
		self.aci_range_combobox.setCurrentText(settings.range_val)
		self.aci_resol_spinbox.setValue(settings.resolution)
		self.aci_filter_combobox.setCurrentText(settings.rms_filter)
		# The frequency path is set before the signal path, an ac signal path
		# forces it to ac
		self.aci_fac_radiobutton.setChecked(settings.frequency_path_coupling == gui_values.AC_PATH_COUPLING_AC)
		self.aci_fdc_radiobutton.setChecked(settings.frequency_path_coupling == gui_values.AC_PATH_COUPLING_DC)
		self.aci_sac_radiobutton.setChecked(settings.signal_path_coupling == gui_values.AC_PATH_COUPLING_AC)
		self.aci_sdc_radiobutton.setChecked(settings.signal_path_coupling == gui_values.AC_PATH_COUPLING_DC)
		self.aci_secread_combobox.setCurrentText(settings.secondary_reading)
		self.aci_off_radiobutton.setChecked(settings.frequency_path_bandwidth_limit == gui_values.AC_BANDWIDTH_LIMIT_OFF)
		self.aci_on_radiobutton.setChecked(settings.frequency_path_bandwidth_limit == gui_values.AC_BANDWIDTH_LIMIT_ON)
		self.aci_count_combobox.setCurrentText(settings.counter_gate)
		self.aci_pktpk_combobox.setCurrentText(settings.peak_to_peak)
		self._update_aci_path_controls(settings.signal_path_coupling == gui_values.AC_PATH_COUPLING_AC)
		self._update_aci_peak_to_peak_control(settings.secondary_reading)

	def set_ohms_settings(self, settings: OhmsSettings):
		# The mode is set first: through _update_ohms_controls it replaces the
		# range items and enables the filter
		self.ohms_mode_combobox.setCurrentText(settings.mode)
		self.ohms_range_combobox.setCurrentText(settings.range_val)
		self.ohms_resol_spinbox.setValue(settings.resolution)
		self.ohms_lolon_radiobutton.setChecked(settings.low_current)
		self.ohms_loloff_radiobutton.setChecked(not settings.low_current)
		self.ohms_man_radiobutton.setChecked(settings.aperture_mode == gui_values.APERTURE_MAN)
		self.ohms_autofast_radiobutton.setChecked(settings.aperture_mode == gui_values.APERTURE_FAST)
		self.ohms_auto_radiobutton.setChecked(settings.aperture_mode == gui_values.APERTURE_AUTO)
		self.ohms_time_radiobutton.setValue(settings.time)
		self.ohms_fillon_radiobutton.setChecked(settings.filter)
		self.ohms_filoff_radiobutton.setChecked(not settings.filter)

	def set_digitize_settings(self, settings: DigitizeSettings):
		# The signal is set first: through _update_digitize_controls it replaces
		# the range and coupling items
		self.digi_tens_radiobutton.setChecked(settings.signal == gui_values.DIGI_SIGNAL_VOLTAGE)
		self.digi_curr_radiobutton.setChecked(settings.signal == gui_values.DIGI_SIGNAL_CURRENT)
		self.digi_range_combobox.setCurrentText(settings.range_val)
		self.digi_coupimp_combobox.setCurrentText(settings.coupling_impedance)
		self.digi_filt_combobox.setCurrentText(settings.filter)
		self.digi_aper_spinbox.setValue(settings.aperture)