import pyvisa
import logging
# Unused: only the commented digit resolution helpers need it
# import math
from Fluke8588A.instrument import scpi
#CLASSE DEL DMM Fluke 8588A
class Fluke8588A():
	"""
	Class for communicating with Fluke 8588A DMM
	
	Public Methods:
	identify() : returns read value of *IDN? query
	write(text) : writes command to instrument
	query(text) : write and read in a single command
	read() : outputs measurement with ":READ?" query
	reset() : resets instrument to power on settings
	close() : close the connection
	
	Configuration Methods:
	set_dcv(range_mode, range_val, resolution_val, zin_val, aperture_mode, time_val) : set DC voltage mode, returns the values read back
	set_dci(range_mode, range_val, resolution_val, aperture_mode, time_val) : set DC current mode, returns the values read back
	set_acv(range_mode, range_val, resolution_val, bandwidth, filter_val, coupling_signal, ...) : set AC voltage mode, returns the values read back
	set_aci(range_mode, range_val, resolution_val, filter_val, coupling_signal, ...) : set AC current mode, returns the values read back
	set_ohms(measurement, range_mode, range_val, resolution_val, ...) : set 2-wire/4-wire ohms mode, returns the values read back
	set_digitize(measurement, range_val, coupling, filter_val, aperture) : set digitize voltage/current mode, returns the values read back
	select_function(root) : selects the function of root if not already active
	check_errors() : empties the error queue, raises if it held errors
	setRange(root, value) / getRange(root) : set/get measurement range
	setResolutionValue(root, value) / getResolutionValue(root) : set/get absolute resolution
	setTime(root, value) / getTime(root) : set/get aperture value in seconds
	setImpedence(root, value) / getImp(root) : set/get input impedance
	setRangeMode(root, value) / getRangeMode(root) : set/get range mode ("AUTO" or "MAN")
	setApertureMode(root, value) / getApertureMode(root) : set/get aperture mode ("AUTO", "FAST", or "MAN")
	"""

	def __init__(self, address):
		logging.info(__name__ + ' : Initializing instrument Fluke 8588A')
		self.is_connected = False
		self.__connect(address)
		self._instr.timeout = scpi.TIMEOUT_MS
		self._line_frequency = None
		self.reset()
		idn_string = self.identify()
		logging.info("Instrument %s successfully initialized." % idn_string)

	def __connect(self, address): #private to be only used by init
		self._rm = pyvisa.ResourceManager()
		self._address = address
		self._instr = self._rm.open_resource(address)
		self.is_connected = True
		
	def identify(self):
		'''
		Sends query *IDN?
		Input:
			none
		Output:
			machine identifiers 
		'''
		return self.query("*IDN?")

	def get_line_frequency(self) -> float:
		"""Return the instrument power-line frequency in hertz."""
		if self._line_frequency is None:
			self._line_frequency = float(self.query(":SYST:LFR?").strip())
		return self._line_frequency

	def write(self, text):
		'''
		Write function
		Input:
			command text
		Output:
			none
		'''  
		self._instr.write(text)


	def query(self, text):
		'''
		Query function
		Input:
			command text
		Output:
			text
		'''  
		return self._instr.query(text)
		
	
	def read(self):
		'''
		Read function
		Input:
			none
		Output:
			text
		'''  
		return self.query(":READ?")
						
	def reset(self):
		'''
		Return Fluke 8588A to power up state...
		Input:
			none
		Output:
			none
		'''        
		self.write("*RST")
	
	def close(self):
		'''
		Closes connection with machine
		Input:
			none
		Output:
			none
		'''
		self._instr.close()
		self._rm.close()
		self.is_connected = False

	def select_function(self, root):
		'''
		Selects the measurement function of root, only if not already active:
		selecting it again reloads its settings and can drop the commands that
		follow (seen in ACV: a RANG written right after was ignored)
		Input:
			root : SCPI root string e.g. ":VOLT:DC"
		Output:
			none
		'''
		function = root[1:] #[1:] serve a rimuovere il : dal root, cosi da avere la formattazione corretta per la stringa
		# FUNC? omits the default :DC and the digitize default :VOLT, e.g.
		# "VOLT" for VOLT:DC and "DIG" for DIG:VOLT
		active = self.query(":FUNC?").strip().strip('"')
		if active not in (function, function.removesuffix(":DC"), function.removesuffix(":VOLT")):
			self.write(":FUNC \"" + function + "\"")

	def check_errors(self):
		'''
		Empties the instrument error queue
		Input:
			none
		Output:
			none, raises RuntimeError listing the queued errors if any
		'''
		errors = []
		for _ in range(scpi.ERROR_QUEUE_MAX_READS):
			answer = self.query(":SYST:ERR?").strip()
			if int(answer.split(",", 1)[0]) == 0:
				break
			errors.append(answer)
		if errors:
			raise RuntimeError("Instrument error: " + "; ".join(errors))

	def set_dcv(self, range_mode, range_val, resolution_val, zin_val, aperture_mode, time_val):
		'''
		Set the machine to dcv mode, and set up parameters
		Input:
			range_mode    : "AUTO" or "MAN"
			range_val     : manual range; with "AUTO" it is the range the
			                resolution refers to, then autorange is enabled
			resolution_val: absolute resolution on range_val
			zin_val       : "AUTO", "1M" or "10M"
			aperture_mode : "AUTO", "FAST" or "MAN"
			time_val      : aperture in seconds, written only with "MAN"
		Output:
			dict, values read back from the instrument after all writes
		'''
		root=scpi.ROOT_DCV
		self.write("*CLS")
		self.select_function(root)
		# RES is interpreted on the active range and kept in digits when the
		# range changes, so it is written on a manual range before autorange
		self.setRange(root, range_val)
		self.setResolutionValue(root, resolution_val)
		self.setRangeMode(root, range_mode)
		self.setImpedence(root, zin_val)
		self.setApertureMode(root, aperture_mode)
		if aperture_mode == scpi.APERTURE_MODE_MAN:
			self.setTime(root, time_val)
		self.check_errors()
		# Read back only after all writes: a later command can change an earlier value
		return {
			"range_mode": self.getRangeMode(root),
			"range_val": self.getRange(root),
			"resolution": self.getResolutionValue(root),
			"zin": self.getImp(root),
			"aperture_mode": self.getApertureMode(root),
			"time": self.getTime(root),
		}

	def set_dci(self, range_mode, range_val, resolution_val, aperture_mode, time_val):
		'''
		Set the machine to dci mode, and set up parameters
		Input:
			range_mode    : "AUTO" or "MAN"
			range_val     : manual range; with "AUTO" it is the range the
			                resolution refers to, then autorange is enabled
			resolution_val: absolute resolution on range_val
			aperture_mode : "AUTO", "FAST" or "MAN"
			time_val      : aperture in seconds, written only with "MAN"
		Output:
			dict, values read back from the instrument after all writes
		'''
		root=scpi.ROOT_DCI
		self.write("*CLS")
		self.select_function(root)
		# RES is interpreted on the active range and kept in digits when the
		# range changes, so it is written on a manual range before autorange
		self.setRange(root, range_val)
		self.setResolutionValue(root, resolution_val)
		self.setRangeMode(root, range_mode)
		self.setApertureMode(root, aperture_mode)
		if aperture_mode == scpi.APERTURE_MODE_MAN:
			self.setTime(root, time_val)
		self.check_errors()
		# Read back only after all writes: a later command can change an earlier value
		return {
			"range_mode": self.getRangeMode(root),
			"range_val": self.getRange(root),
			"resolution": self.getResolutionValue(root),
			"aperture_mode": self.getApertureMode(root),
			"time": self.getTime(root),
		}

	def set_aci(self, range_mode, range_val, resolution_val, filter_val, coupling_signal, counter_coupling, counter_blimit, counter_gate, secondary, secondary_method):
		'''
		Set the machine to aci mode, and set up parameters
		Input:
			range_mode      : "AUTO" or "MAN"
			range_val       : manual range; with "AUTO" it is the range the
			                  resolution refers to, then autorange is enabled
			resolution_val  : absolute resolution on range_val
			filter_val      : rms filter in hertz
			coupling_signal : "AC" or "DC", the impedance is always auto
			counter_coupling: "AC" or "DC", written only with a dc signal path
			counter_blimit  : 0 or 1, frequency path bandwidth limit
			counter_gate    : "AUTO" or gate in seconds
			secondary       : secondary reading, e.g. "OFF", "FREQ", "PTP"
			secondary_method: peak to peak method, e.g. "MEAS", "SINE"
		Output:
			dict, values read back from the instrument after all writes
		'''
		root = scpi.ROOT_ACI
		self.write("*CLS")
		self.select_function(root)
		# RES is interpreted on the active range and kept in digits when the
		# range changes, so it is written on a manual range before autorange
		self.setRange(root, range_val)
		self.setResolutionValue(root, resolution_val)
		self.setRangeMode(root, range_mode)
		# Switching the signal path to ac resets the frequency path to ac
		self.setCoupling(root, coupling_signal)
		if coupling_signal == scpi.ACI_COUPLING_DC:
			self.setCounterCoupling(root, counter_coupling)
		self.setRmsFilter(root, filter_val)
		self.setBlimit(root, counter_blimit)
		# The auto gate follows the rms filter, so it is written after it
		if counter_gate == scpi.AC_COUNTER_GATE_AUTO:
			self.setGateMode(root, True)
		else:
			self.setGateMode(root, False)
			self.setCounterGate(root, counter_gate)
		self.setSecondary(root, secondary)
		self.setSecondaryMethod(root, secondary_method)
		self.check_errors()
		# Read back only after all writes: a later command can change an earlier value
		return {
			"range_mode": self.getRangeMode(root),
			"range_val": self.getRange(root),
			"resolution": self.getResolutionValue(root),
			"rms_filter": self.getRmsFilter(root),
			"signal_path_coupling": self.getCoupling(root),
			"secondary_reading": self.getSecondary(root),
			"frequency_path_coupling": self.getCounterCoupling(root),
			"frequency_path_bandwidth_limit": self.getBlimit(root),
			"counter_gate": (
				scpi.AC_COUNTER_GATE_AUTO
				if self.getGateMode(root)
				else self.getCounterGate(root)
			),
			"peak_to_peak": self.getSecondaryMethod(root),
		}

	def init_shunt(self, root, shunt_list_index, shunt_sort=None, add_shunt_attributes=None, add_shunt_differences=None):
		'''
		Initialize shunt configuration for current measurements
		Input:
			root : SCPI root string e.g. ":CURR:AC"
			shunt_list_index : int, index of the shunt in the shunt list
			shunt_sort : optional str, sort order ("MCURrent", "ASSet", "SERial")
			add_shunt_attributes : optional str, new shunt attributes to add
			add_shunt_differences : optional list of tuples [(frequency, difference), ...] to add AC-DC differences
		Output:
			none
		'''
		if add_shunt_attributes is not None:
			self.addShunt(root, add_shunt_attributes)
		
		if shunt_sort is not None:
			self.setShuntSort(root, shunt_sort)
		
		self.pickShunt(root, shunt_list_index)
		
		if add_shunt_differences is not None:
			for frequency, difference in add_shunt_differences:
				self.addShuntDifference(root, frequency, difference)

	def set_acv(self, range_mode, range_val, resolution_val, bandwidth, filter_val, coupling_signal, counter_coupling, counter_blimit, counter_gate, secondary, secondary_method):
		'''
		Set the machine to acv mode, and set up parameters
		Input:
			range_mode      : "AUTO" or "MAN"
			range_val       : manual range; with "AUTO" it is the range the
			                  resolution refers to, then autorange is enabled
			resolution_val  : absolute resolution on range_val
			bandwidth       : "WIDE" or "EHF"
			filter_val      : rms filter in hertz
			coupling_signal : "AC1M", "AC10M", "DC1M", "DC10M" or "DCA"
			counter_coupling: "AC" or "DC", written only with a dc signal path
			counter_blimit  : 0 or 1, frequency path bandwidth limit
			counter_gate    : "AUTO" or gate in seconds
			secondary       : secondary reading, e.g. "OFF", "FREQ", "PTP"
			secondary_method: peak to peak method, e.g. "MEAS", "SINE"
		Output:
			dict, values read back from the instrument after all writes
		'''
		root=scpi.ROOT_ACV
		self.write("*CLS")
		self.select_function(root)
		# Written first: the operating mode can change the other settings
		self.setBwidth(root, bandwidth)
		# RES is interpreted on the active range and kept in digits when the
		# range changes, so it is written on a manual range before autorange
		self.setRange(root, range_val)
		self.setResolutionValue(root, resolution_val)
		self.setRangeMode(root, range_mode)
		# An ac signal path forces the frequency path to ac
		self.setCouplingSignal(root, coupling_signal)
		if coupling_signal in scpi.AC_DC_SIGNAL_COUPLINGS:
			self.setCounterCoupling(root, counter_coupling)
		self.setRmsFilter(root, filter_val)
		self.setBlimit(root, counter_blimit)
		# The auto gate follows the rms filter, so it is written after it
		if counter_gate == scpi.AC_COUNTER_GATE_AUTO:
			self.setGateMode(root, True)
		else:
			self.setGateMode(root, False)
			self.setCounterGate(root, counter_gate)
		self.setSecondary(root, secondary)
		self.setSecondaryMethod(root, secondary_method)
		self.check_errors()
		# Read back only after all writes: a later command can change an earlier value
		return {
			"range_mode": self.getRangeMode(root),
			"range_val": self.getRange(root),
			"resolution": self.getResolutionValue(root),
			"rms_filter": self.getRmsFilter(root),
			"coupling_impedance": self.getCouplingSignal(root),
			"secondary_reading": self.getSecondary(root),
			"frequency_path_coupling": self.getCounterCoupling(root),
			"frequency_path_bandwidth_limit": self.getBlimit(root),
			"counter_gate": (
				scpi.AC_COUNTER_GATE_AUTO
				if self.getGateMode(root)
				else self.getCounterGate(root)
			),
			"bandwidth": self.getBwidth(root),
			"peak_to_peak": self.getSecondaryMethod(root),
		}
	
	def set_ohms(self, measurement, range_mode, range_val, resolution_val, filter_val, low_current, aperture_mode, time_val):
		'''
		Set the machine to 2-wire (RES) or 4-wire (FRES) ohms, and set up parameters
		Input:
			measurement   : a key of scpi.OHM_MEASUREMENTS, e.g. scpi.OHM_4W_TRUE
			range_mode    : "AUTO" or "MAN"
			range_val     : manual range, ignored with "AUTO"
			resolution_val: absolute resolution on scpi.OHM_RESOLUTION_RANGE
			filter_val    : bool, filter on/off (shared by RES and FRES)
			low_current   : bool, low current on/off (kept per function and mode)
			aperture_mode : "AUTO", "FAST" or "MAN"
			time_val      : aperture in seconds, written only with "MAN"
		Output:
			dict, values read back from the instrument after all writes
		'''
		root, mode = scpi.OHM_MEASUREMENTS[measurement]
		self.write("*CLS")
		self.select_function(root)
		# Written first: TRUE limits the range, and LOWI is kept per mode
		self.setWireMode(root, mode)
		# RES is kept in digits when the range changes, so it is written on a
		# range that accepts every digit count, then the range is set
		self.setRange(root, scpi.OHM_RESOLUTION_RANGE)
		self.setResolutionValue(root, resolution_val)
		if range_mode == scpi.RANGE_MODE_MAN_STR:
			self.setRange(root, range_val)
		self.setRangeMode(root, range_mode)
		self.setFilter(root, filter_val)
		self.setLowCurrentMode(root, low_current)
		self.setApertureMode(root, aperture_mode)
		if aperture_mode == scpi.APERTURE_MODE_MAN:
			self.setTime(root, time_val)
		self.check_errors()
		wire_mode = self.getWireMode(root)
		# Read back only after all writes: a later command can change an earlier value
		return {
			"range_mode": self.getRangeMode(root),
			"range_val": self.getRange(root),
			"resolution": self.getResolutionValue(root),
			"mode": next(
				key for key, value in scpi.OHM_MEASUREMENTS.items() if value == (root, wire_mode)
			),
			"filter": self.getFilter(root),
			"low_current": self.getLowCurrentMode(root),
			"aperture_mode": self.getApertureMode(root),
			"time": self.getTime(root),
		}

	def set_digitize(self, measurement, range_val, coupling, filter_val, aperture):
		'''
		Set the machine to digitize voltage or current, and set up parameters
		Input:
			measurement: a key of scpi.DIGI_MEASUREMENTS, e.g. scpi.DIGI_VOLTAGE
			range_val  : range, digitize has no autorange
			coupling   : voltage "AC1M", "AC10M", "DC1M", "DC10M" or "DCA";
			             current "AC" or "DC"
			filter_val : low pass filter "OFF", "100K" or "3MHZ"
			aperture   : aperture in seconds, 0 to 3 ms
		Output:
			dict, values read back from the instrument after all writes
		'''
		root = scpi.DIGI_MEASUREMENTS[measurement]
		self.write("*CLS")
		self.select_function(root)
		self.setRange(root, range_val)
		if root == scpi.ROOT_DIGIVOLTAGE:
			self.setCouplingSignal(root, coupling)
		else:
			self.setCoupling(root, coupling)
		# Filter and aperture are shared by voltage and current
		self.setDigitizeFilter(scpi.ROOT_DIGITIZE, filter_val)
		self.setDigitizeAperture(scpi.ROOT_DIGITIZE, aperture)
		self.check_errors()
		# Read back only after all writes: a later command can change an earlier value
		return {
			"signal": measurement,
			"range_val": self.getRange(root),
			"coupling_impedance": (
				self.getCouplingSignal(root)
				if root == scpi.ROOT_DIGIVOLTAGE
				else self.getCoupling(root)
			),
			"filter": self.getDigitizeFilter(scpi.ROOT_DIGITIZE),
			# The instrument rounds the aperture up to its step
			"aperture": self.getTime(scpi.ROOT_DIGITIZE),
		}

	'''
	Legacy OHMS initializers: replaced by set_ohms, they use the digit
	resolution (setResolution) and do not read back.
	def init_resistance(self, aperture_mode, time_val, mode_val, low_mode_val, range_mode, range_val, resolution_val, filter_val):
		root=scpi.ROOT_RESISTANCE
		self.write(":FUNC \"" + root[1:] + "\"") #[1:] serve a rimuovere il : dal root, cosi da avere la formattazione corretta per la stringa
		self.setWireMode(root, mode_val)
		self.setLowCurrentMode(root, low_mode_val)
		self.setRangeMode(root, range_mode)
		self.setRange(root, range_val)
		self.setResolution(root, resolution_val)
		self.setFilter(root, filter_val)
		self.setTime(root, time_val)
		self.setApertureMode(root, aperture_mode)
	

	def init_fresistance(self, aperture_mode, time_val, mode_val, low_mode_val, range_mode, range_val, resolution_val, filter_val):
		root=scpi.ROOT_FRESISTANCE
		self.write(":FUNC \"" + root[1:] + "\"") #[1:] serve a rimuovere il : dal root, cosi da avere la formattazione corretta per la stringa
		self.setWireMode(root, mode_val)
		self.setLowCurrentMode(root, low_mode_val)
		self.setRangeMode(root, range_mode)
		self.setRange(root, range_val)
		self.setResolution(root, resolution_val)
		self.setFilter(root, filter_val)
		self.setTime(root, time_val)
		self.setApertureMode(root, aperture_mode)
	'''

	'''
	Legacy trigger initializer. Use the controller's trigger settings path instead.
	def init_trigger_base(self, event, count, ecount, delay, holdoff):
		root = scpi.ROOT_TRIGGER
		self.setReset(root)
		self.setCount(root, count)
		self.setCount(root, ecount)
		self.setDelay(root, delay)
		self.setHoldoff(root, holdoff)
	'''


	def getApertureMode(self, root):
		'''
		Get aperture mode for given root
		Input:
			Root
		Output:
			string, "AUTO", "FAST", "MAN"
		'''
		return self.query(root+":APER:MODE?").strip()
	def setApertureMode(self, root, value):
		'''
		Sets aperture mode for given root.
		Input:
			root  : SCPI root string e.g. ":VOLT:DC"
			value : "AUTO", "FAST", or "MAN"
		Output:
			string, set value: "AUTO", "FAST", or "MAN"
		'''
		if value not in scpi.VALID_APERTURE_MODES:
			raise ValueError(
				f"Invalid aperture mode '{value}'. "
				f"Expected one of {scpi.VALID_APERTURE_MODES}"
			)
		cmd = root + ":APER:MODE " + str(value)
		logging.info(f"[APERTURE] Sending: {cmd}")
		self.write(cmd)
		result = self.getApertureMode(root)
		logging.info(f"[APERTURE] Query result: {result}")
		return result
	
	def getTime(self, root):
		'''
		Get aperture value in seconds for given root
		Input:
			root
		Output:
			float, set value
		'''
		return float(self.query(root+":APER?"))
	def setTime(self, root, value):
		'''
		Sets aperture value in seconds for given root.
		Input:
			root  : SCPI root string e.g. ":VOLT:DC"
			value : aperture value in seconds
		Output:
			float, accepted aperture value in seconds
		'''
		aperture = float(value)
		if aperture <= 0:
			raise ValueError(f"Aperture value must be positive, got {value}")
		self.write(root + ":APER " + str(aperture))
		return self.getTime(root)

	def getImp(self, root):
		'''
		Get Impedence value for given root
		Input:
			root
		Output:
			string, set value
		'''
		return self.query(root+":IMP?").strip()
	def setImpedence(self, root, value):
		'''
		Sets input impedance for given root.
		Input:
			root  : SCPI root string e.g. ":VOLT:DC"
			value : "AUTO", "1M", or "10M"
		Output:
			string, set value: "AUTO", "1M", or "10M"
		'''
		if value not in scpi.VALID_DCV_IMPEDANCES:
			raise ValueError(
				f"Invalid impedance '{value}'. "
				f"Expected one of {scpi.VALID_DCV_IMPEDANCES}"
			)
		self.write(root + ":IMP " + str(value))
		return self.getImp(root)
	

	def getRangeMode(self, root):
		'''
		Get range mode for given root
		Input:
			root, value
		Output:
			string, "AUTO" or "MAN"
		'''
		response = int(float(self.query(root+":RANG:AUTO?")))
		if response != 0:
			return scpi.RANGE_MODE_AUTO_STR
		elif response == 0:
			return scpi.RANGE_MODE_MAN_STR
		else:
			raise ValueError(f"Unexpected range mode value returned by machine: {response}")
	def setRangeMode(self, root, value):
		'''
		Sets range mode for given root.
		Input:
			root  : SCPI root string e.g. ":VOLT:DC"
			value : "AUTO" or "MAN"
		Output:
			string, set value: "AUTO" or "MAN"
		'''
		if value == scpi.RANGE_MODE_AUTO_STR:
			converted_value = scpi.RANGE_MODE_AUTO
		elif value == scpi.RANGE_MODE_MAN_STR:
			converted_value = scpi.RANGE_MODE_MAN
		else:
			raise ValueError(
				f"Invalid range mode '{value}'. "
				f"Expected '{scpi.RANGE_MODE_AUTO_STR}' "
				f"or '{scpi.RANGE_MODE_MAN_STR}'"
			)
		self.write(root + ":RANG:AUTO " + str(converted_value))
		return self.getRangeMode(root)
	

	def getRange(self, root):
		'''
		Get range value for given root
		Input:
			root
		Output:
			float, set value
		'''
		return float(self.query(root+":RANG?").strip())
	def setRange(self, root, value):
		'''
		Set range value for given root
		Input:
			root, desired value
		Output:
			string, set value
		'''
		self.write(root+":RANG "+str(value))
		return self.getRange(root)
	
	"""
	Legacy digit resolution (10**-digits): replaced by setResolutionValue /
	getResolutionValue, the digits are converted by the Translator on the
	range. Only the commented init_resistance/init_fresistance used it.
	def getResolution(self, root):
		'''
		Get resolution value for given root
		Input:
			root
		Output:
			int, digit count (see scpi.VALID_RESOLUTION_DIGITS[root])
		'''
		raw_resolution = float(self.query(root+":RES?"))
		return self.__anti_convert_resolution(raw_resolution)
	def setResolution(self, root, value):
		'''
		Sets resolution in digits for given root.
		Converts digit count to the resolution value the instrument expects.
		Input:
			root  : SCPI root string e.g. ":VOLT:DC", must be a key of
			        scpi.VALID_RESOLUTION_DIGITS
			value : int or str, number of digits allowed for root
			        (scpi.VALID_RESOLUTION_DIGITS[root])
		Output:
			float, set value in digits

		Example:
			setResolution(":VOLT:DC", 4) --> measures 1.2348 V  (returns 4)
			setResolution(":VOLT:DC", 6) --> measures 1.234778 V (returns 6)
		'''
		digit_value = int(value)
		valid_digits = scpi.VALID_RESOLUTION_DIGITS.get(root)
		if valid_digits is None:
			raise ValueError(f"Resolution in digits is not supported for root {root!r}")
		if digit_value not in valid_digits:
			raise ValueError(
				f"{root} resolution must be one of {valid_digits}, got {digit_value}"
			)

		converted_resolution = self.__convert_resolution(digit_value)
		self.write(root + ":RES " + str(converted_resolution))
		return self.getResolution(root)
	"""

	def setResolutionValue(self, root, value):
		"""Set an absolute resolution value as specified by the SCPI manual."""
		resolution_value = float(value)
		if resolution_value <= 0:
			raise ValueError(f"Resolution must be positive, got {value}")
		self.write(root + ":RES " + str(resolution_value))
		return self.getResolutionValue(root)

	def getResolutionValue(self, root):
		"""Get the absolute resolution value for given root."""
		return float(self.query(root + ":RES?").strip())

	'''
	Legacy, helpers of the commented setResolution/getResolution.
	def __convert_resolution(self, value):
		return 10**(-value)

	def __anti_convert_resolution(self, value):
		# Check if value is already in digit format (4-8)
		# This handles machines that return resolution as digit count directly
		if value >= 4 and value <= 8 and value == int(value):
			return int(value)
		
		# Otherwise, convert the absolute resolution (1E-4 -> 4 digits).
		resolution = float(value)
		if resolution <= 0 or not math.isfinite(resolution):
			raise ValueError(f"Invalid resolution from instrument: {value}")
		digits = round(-math.log10(resolution))
		if math.isclose(resolution, 10 ** -digits, rel_tol=1e-9, abs_tol=1e-15):
			return digits
		raise ValueError(f"Unexpected resolution from instrument: {value}")
	'''

	#ACI
	def getBlimit(self, root):
		return int(float(self.query(f"{root}:COUNter:BLIMit?")))

	def setBlimit(self, root, value:bool):
		self.write(f"{root}:COUNter:BLIMit {int(value)}")
		return self.getBlimit(root)

	def getCounterCoupling(self, root):
		return self.query(f"{root}:COUNter:COUPling?").strip()

	def setCounterCoupling(self, root, value):
		self.write(f"{root}:COUNter:COUPling {value}")
		return self.getCounterCoupling(root)

	def getGateMode(self, root):
		return bool(int(float(self.query(f"{root}:COUNter:GATE:AUTO?"))))

	def setGateMode(self, root, value:bool):
		self.write(f"{root}:COUNter:GATE:AUTO {int(value)}")
		return self.getGateMode(root)

	def getFilter(self, root):
		return bool(int(self.query(f"{root}:FILTer?").strip()))

	def setFilter(self, root, value:bool):
		self.write(f"{root}:FILTer {int(value)}")
		return self.getFilter(root)

	# DIGITIZE, root scpi.ROOT_DIGITIZE
	def getDigitizeFilter(self, root):
		return self.query(f"{root}:FILTer?").strip()

	def setDigitizeFilter(self, root, value):
		self.write(f"{root}:FILTer {value}")
		return self.getDigitizeFilter(root)

	def setDigitizeAperture(self, root, value):
		# Not setTime: 0 is a valid digitize aperture
		aperture = float(value)
		if not scpi.DIGI_APERTURE_MIN <= aperture <= scpi.DIGI_APERTURE_MAX:
			raise ValueError(
				f"Digitize aperture must be between {scpi.DIGI_APERTURE_MIN} "
				f"and {scpi.DIGI_APERTURE_MAX} s, got {value}"
			)
		self.write(f"{root}:APERture {aperture}")
		return self.getTime(root)

	def getRmsFilter(self, root):
		'''
		Get the AC rms filter for given root
		Input:
			root
		Output:
			float, filter in hertz
		'''
		return float(self.query(f"{root}:FILTer?"))

	def setRmsFilter(self, root, value):
		'''
		Sets the AC rms filter for given root; unlike setFilter it is a
		frequency, the closest discrete setting is selected
		Input:
			root  : SCPI root string e.g. ":VOLT:AC"
			value : filter in hertz (0.1, 1, 10, 40, 100, 1000)
		Output:
			float, set value in hertz
		'''
		self.write(f"{root}:FILTer {float(value)}")
		return self.getRmsFilter(root)

	def getCounterGate(self, root):
		return float(self.query(f"{root}:COUNter:GATE?"))

	def setCounterGate(self, root, value):
		self.write(f"{root}:COUNter:GATE {value}")
		return self.getCounterGate(root)

	def getSecondary(self, root):
		return self.query(f"{root}:SECondary?").strip()
	def setSecondary(self, root, value:str):
		self.write(f"{root}:SECondary {value}")
		return self.getSecondary(root)

	def getSecondaryMethod(self, root):
		return self.query(f"{root}:SECondary:METHod?").strip()

	def setSecondaryMethod(self, root, value:str):
		self.write(f"{root}:SECondary:METHod {value}")
		return self.getSecondaryMethod(root)

	def getShunt(self, root, list_index=None):
		if list_index is not None:
			return self.query(f"{root}:SHUNt? {list_index}")
		return self.query(f"{root}:SHUNt?")

	def addShunt(self, root, attributes:str):
		self.write(f"{root}:SHUNt:ADD {attributes}")

	def getShuntCount(self, root):
		return self.query(f"{root}:SHUNt:COUNt?")

	def getShuntDifference(self, root):
		return self.query(f"{root}:SHUNt:DIFFerence?")

	def addShuntDifference(self, root, frequency, difference):
		self.write(f"{root}:SHUNt:DIFFerence:ADD {frequency}, {difference}")

	def removeShuntDifference(self, root, diff_index):
		self.write(f"{root}:SHUNt:DIFFerence:REMove {diff_index}")

	def getShuntList(self, root):
		return self.query(f"{root}:SHUNt:LIST?")

	def modifyShunt(self, root, list_index, attributes:str):
		self.write(f"{root}:SHUNt:MODify {list_index}, {attributes}")

	def pickShunt(self, root, list_index):
		self.write(f"{root}:SHUNt:PICK {list_index}")

	def getShuntPick(self, root):
		return self.query(f"{root}:SHUNt:PICK?")

	def removeShunt(self, root, list_index):
		self.write(f"{root}:SHUNt:REMove {list_index}")

	def setShuntSort(self, root, sort_order:str):
		self.write(f"{root}:SHUNt:SORT {sort_order}")

	def getShuntSort(self, root):
		return self.query(f"{root}:SHUNt:SORT?")

	#ACV
	def getBwidth(self, root):
		return self.query(f"{root}:BWIDth?").strip()

	def setBwidth(self, root, value):
		self.write(f"{root}:BWIDth {value}")
		return self.getBwidth(root)

	def getCouplingSignal(self, root):
		return self.query(f"{root}:COUPling:SIGNal?").strip()

	def setCouplingSignal(self, root, value):
		self.write(f"{root}:COUPling:SIGNal {value}")
		return self.getCouplingSignal(root)
	
	#IMMEDIATE
	def getContinuos(self, root):
		return self.query(f"{root}:CONT?")
	def setContinuos(self, root, state:bool):
			return self.write(f"{root}:CONT {state}")

	def getEpochStart(self, root):
		return self.query(f"{root}:EPOC:STAR?")
	def setEpochStart(self, root, date:str):
		return self.write(f"{root}:EPOC:STAR {date}")

	def getEpochStop(self, root):
		return self.query(f"{root}:EPOC:STOP?")
	def setEpochStop(self, root, date:str):
		return self.write(f"{root}:EPOC:STOP {date}")

	#ARM1 ARM2
	def getCount(self, root):
		return self.query(f"{root}:COUNt?")
	def setCount(self, root, value):
		self.write(f"{root}:COUNt {value}")
		return self.getCount(root)

	# Also the ACI signal path coupling (:CURR:AC:COUP)
	def getCoupling(self, root):
		return self.query(f"{root}:COUP?").strip()
	def setCoupling(self, root, coupling:str):
		self.write(f"{root}:COUP {coupling}")
		return self.getCoupling(root)
	
	def getDelay(self, root):
		return self.query(f"{root}:DELay?")
	def setDelay(self, root, value):
		self.write(f"{root}:DELay {value}")
		return self.getDelay(root)
	
	def getDelayMode(self, root):
		return self.query(f"{root}:DELay:AUTO?")
	def setDelayMode(self, root, value:bool):
		state = "ON" if value else "OFF"
		self.write(f"{root}:DELay:AUTO {state}")
		return self.getDelayMode(root)
	
	def getEcount(self, root):
		return self.query(f"{root}:ECOunt?")
	def setEcount(self, root, value):
		self.write(f"{root}:ECOunt {value}")
		return self.getEcount(root)

	def getExternal(self, root):
		return self.query(f"{root}:EXTernal?")
	def setExternal(self, root, value):
		self.write(f"{root}:EXTernal {value}")
		return self.getExternal(root)

	def setImmediate(self, root):
		self.write(f"{root}:IMMediate")

	def getLevel(self, root):
		return self.query(f"{root}:LEVel?")
	def setLevel(self, root, value):
		self.write(f"{root}:LEVel {value}")
		return self.getLevel(root)

	def resetTrigger(self, root):
		self.write(f"{root}:RESet")

	def setSignal(self, root):
		self.write(f"{root}:SIGNal")

	def getSlope(self, root):
		return self.query(f"{root}:SLOPe?")
	def setSlope(self, root, value):
		self.write(f"{root}:SLOPe {value}")
		return self.getSlope(root)

	def getSource(self, root):
		return self.query(f"{root}:SOURce?")
	def setSource(self, root, value):
		self.write(f"{root}:SOURce {value}")
		return self.getSource(root)

	def getTimer(self, root):
		return self.query(f"{root}:TIMer?")
	def setTimer(self, root, value):
		self.write(f"{root}:TIMer {value}")
		return self.getTimer(root)

	# TRIGGER 
	def getHoldoffAuto(self, root):
		return self.query(f"{root}:HOLDoff:AUTO?")
	def setHoldoffAuto(self, root, value: bool):
		state = "ON" if value else "OFF"
		self.write(f"{root}:HOLDoff:AUTO {state}")
		return self.getHoldoffAuto(root)

	def getHoldoff(self, root):
		return self.query(f"{root}:HOLDoff?")
	def setHoldoff(self, root, value):
		self.write(f"{root}:HOLDoff {value}")
		return self.getHoldoff(root)

	'''
	Unused duplicate of resetTrigger (same <root>:RESet command).
	def setReset(self, root):
		return self.write(f"{root}:RES")
	'''


	"""
	Unused and to be fixed before use: zero() is not an f-string, so it sends
	"{value}" literally, and zeroClear() sends ZERO instead of ZERO:CLEar.
	#ZERO
	def zero(self, value):
		'''
		input: RANGe || ALL;
		Output:  1 || 0;
		Removes residual offsets, applies to active range or function. Returns ‘0’ for success, and ‘1’ for failure;
		'''
		return self.query("SENSe:ZERO {value}")
	
	def zeroClear(self, value):
		'''
		input: RANGe || ALL;
		Output:  1 || 0;
		Clears zero, applies to active range or function. Returns ‘0’ for success, and ‘1’ for failure;
		'''
		return self.query(f"SENSe:ZERO {value}")
	"""

	# RESISTANCE and FRESISTANCE (only change is mode, FRES has TRUE as an extra option)
	def getWireMode(self, root):
		return self.query(f"{root}:MODE?").strip()
	def setWireMode(self, root, value):
		'''
		input: (root, NORM || TRUE), TRUE only with :FRES;
		Output:  NORM || TRUE ;
		Sets the Ohms mode, returns the mode that has been set in machine.
		'''
		self.write(f"{root}:MODE {value}")
		return self.getWireMode(root)

	def getLowCurrentMode(self, root):
		return bool(int(self.query(f"{root}:LOWI?").strip()))
	def setLowCurrentMode(self, root, value:bool):
		'''
		input: (root, bool);
		Output:  bool, set value;
		Sets the Low current mode ON or OFF, the instrument keeps it per
		function and per mode (NORM/TRUE)
		'''
		self.write(f"{root}:LOWI {int(value)}")
		return self.getLowCurrentMode(root)
	