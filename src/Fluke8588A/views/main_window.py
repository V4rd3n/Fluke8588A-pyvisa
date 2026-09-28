from PyQt6 import uic
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QMainWindow
import os, json
from src.Fluke8588A.data.spin_box_values import get_functions, get_dcv_range, get_dci_range, get_dcv_impedence, get_dc_digit_val, get_ohm_modes, get_ohm_range
from src.Fluke8588A.instrument.config import InstrumentConfig
import src.Fluke8588A.instrument.config as config 
from src.Fluke8588A.data.settings import DcvSettings, DciSettings, OhmsSettings
from src.Fluke8588A.views.plot_widget import DmmPlotWidget
main_window_loc = os.path.join(os.path.dirname(__file__), "..", "ui", "mainwindow.ui")
class MainWindow(QMainWindow):
	
	init_requested = pyqtSignal()
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
	append_value = pyqtSignal(float)	

	def __init__(self):
		super().__init__()
		uic.loadUi(main_window_loc, self)
		self.set_mode_visible(self.current_mode)
		self._connect_signals()
		self._init_widgets()
		
	def _connect_signals(self):
		#init set mode
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
		self.trigger_button.pressed.connect(self.trigger_requested) #to be
		 

	def _init_widgets(self):
		self.gpib_addr_spin.setRange(0, 30)
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
		self.plot_widget._connect_signals(self)

	@property
	def current_gpib_address(self)->int:
		return self.gpib_addr_spin.value()

	@property
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

	def _on_dcv_settings_received(self, settings: DcvSettings):
		"""Update UI when settings are received from instrument"""
		self.dcv_range_combo.blockSignals(True)
		self.dcv_res_spin.blockSignals(True)
		self.dcv_zin_combo.blockSignals(True)

		self.dcv_range_combo.setCurrentText(settings.range_val)
		self.dcv_res_spin.setValue(settings.resolution)
		self.dcv_zin_combo.setCurrentText(settings.zin)
		self.dcv_measure_setup_button.setText(settings.aperture_mode)
		self.dcv_time_label.setText(str(settings.time))

		self.dcv_range_combo.blockSignals(False)
		self.dcv_res_spin.blockSignals(False)
		self.dcv_zin_combo.blockSignals(False)

	def _on_dci_settings_received(self, settings: DciSettings):
		"""Update UI when settings are received from instrument"""
		self.dci_range_combo.blockSignals(True)
		self.dci_res_spin.blockSignals(True)

		self.dci_range_combo.setCurrentText(settings.range_val)
		self.dci_res_spin.setValue(settings.resolution)
		self.dci_measure_setup_button.setText(settings.aperture_mode)
		self.dci_time_label.setText(str(settings.time))

		self.dci_range_combo.blockSignals(False)
		self.dci_res_spin.blockSignals(False)

	def _on_ohms_settings_received(self, settings: OhmsSettings):
		"""Update UI when settings are received from instrument"""
		self.ohm_range_combo.blockSignals(True)
		self.ohm_res_spin.blockSignals(True)
		self.ohm_mode_combo.blockSignals(True)
		self.ohm_filter_check.blockSignals(True)
		self.ohm_lowi_check.blockSignals(True)

		self.ohm_range_combo.setCurrentText(settings.range_val)
		self.ohm_res_spin.setValue(settings.resolution)
		self.ohm_mode_combo.setCurrentText(settings.mode)
		self.ohm_filter_check.setChecked(settings.filter)
		self.ohm_lowi_check.setChecked(settings.low_i)
		self.ohm_measure_setup.setText(settings.aperture_mode)
		self.ohm_time_label.setText(str(settings.time))

		self.ohm_range_combo.blockSignals(False)
		self.ohm_res_spin.blockSignals(False)
		self.ohm_mode_combo.blockSignals(False)
		self.ohm_filter_check.blockSignals(False)
		self.ohm_lowi_check.blockSignals(False)