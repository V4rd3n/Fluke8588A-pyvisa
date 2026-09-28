import pyvisa
import logging
from src.Fluke8588A.instrument.config import InstrumentConfig
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
	init_dcv(range_mode, range_val, resolution_val, zin_val, aperture_mode, nplc_val) : initialize DC voltage mode
	setRange(root, value) / getRange(root) : set/get measurement range
	setResolution(root, value) / getResolution(root) : set/get resolution
	setTime(root, value) / getTime(root) : set/get NPLC value (1plc=50Hz in EU)
	setImpedence(root, value) / getImp(root) : set/get input impedance
	setRangeMode(root, value) / getRangeMode(root) : set/get range mode ("AUTO" or "MAN")
	setApertureMode(root, value) / getApertureMode(root) : set/get aperture mode ("AUTO", "FAST", or "MAN")
	"""

	# only GPIB support
	def __init__(self, address):
		logging.info(__name__ + ' : Initializing instrument Fluke 8588A')
		self.is_connected = False
		self.__connect(address)
		self._instr.timeout = InstrumentConfig.TIMEOUT_MS
		self.plc_max = InstrumentConfig.NPLC_MAX
		self.reset()
		idn_string = self.identify()
		logging.info("Instrument %s successfully initialized." % idn_string)

	def __connect(self, address): #private to be only used by init
		rm = pyvisa.ResourceManager()
		self._address = address
		#self._instr = rm.open_resource(InstrumentConfig.GPIB_PREFIX + str(self._address) + InstrumentConfig.GPIB_SUFFIX)
		self._instr = rm.open_resource("USB0::3966::32777::651684161::0::INSTR")
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
		self.is_connected = False

	def init_dcv(self, range_mode, range_val,  resolution_val, zin_val, aperture_mode, time_val):
		'''
		Set the machine to dcv mode, and set up parameters
		'''
		root=InstrumentConfig.ROOT_DCV
		self.write(":FUNC \"" + root[1:] + "\"") #[1:] serve a rimuovere il : dal root, cosi da avere la formattazione corretta per la stringa
		self.setRangeMode(root, range_mode)
		self.setRange(root, range_val)
		self.setResolution(root, resolution_val)
		self.setImpedence(root, zin_val)		
		self.setTime(root, time_val)
		self.setApertureMode(root, aperture_mode)

	def init_dci(self, range_mode, range_val, resolution_val, aperture_mode, time_val):
		root=InstrumentConfig.ROOT_DCI
		self.write(":FUNC \"" + root[1:] + "\"") #[1:] serve a rimuovere il : dal root, cosi da avere la formattazione corretta per la stringa
		self.setRangeMode(root, range_mode)
		self.setRange(root, range_val)
		self.setResolution(root, resolution_val)
		self.setTime(root, time_val)
		self.setApertureMode(root, aperture_mode)

	def init_aci(self, blimit, counter_Coupling, counter_gate, coupling, filter, range_mode, range_val, resolution_val, secondary, secondary_method):
		'''
		Set the machine to aci mode, and set up parameters
		'''
		root = InstrumentConfig.ROOT_ACI
		self.write(":FUNC \"" + root[1:] + "\"") #[1:] serve a rimuovere il : dal root, cosi da avere la formattazione corretta per la stringa
		self.setBlimit(root, blimit)
		self.setCounterCoupling(root, counter_Coupling)
		self.setCounterGate(root, counter_gate)
		self.setCoupling(root, coupling)
		self.setFilter(root, filter)
		self.setRangeMode(root, range_mode)
		self.setRange(root, range_val)
		self.setResolution(root, resolution_val)
		self.setSecondary(root, secondary)
		self.setSecondaryMethod(root, secondary_method)

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

	def init_acv(self, root, blimit, counter_coupling, counter_gate, coupling_signal, filter_val, range_mode, range_val, resolution_val, secondary, secondary_method):
		self.setBlimit(root, blimit)
		self.setCounterCoupling(root, counter_coupling)
		self.setCounterGate(root, counter_gate)
		self.setCouplingSignal(root, coupling_signal)
		self.setFilter(root, filter_val)
		self.setRangeMode(root, range_mode)
		self.setRange(root, range_val)
		self.setResolution(root, resolution_val)
		self.setSecondary(root, secondary)
		self.setSecondaryMethod(root, secondary_method)
	
	def init_resistance(self, aperture_mode, time_val, mode_val, low_mode_val, range_mode, range_val, resolution_val, filter_val):
		root=InstrumentConfig.ROOT_RESISTANCE
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
		root=InstrumentConfig.ROOT_FRESISTANCE
		self.write(":FUNC \"" + root[1:] + "\"") #[1:] serve a rimuovere il : dal root, cosi da avere la formattazione corretta per la stringa
		self.setWireMode(root, mode_val)
		self.setLowCurrentMode(root, low_mode_val)
		self.setRangeMode(root, range_mode)
		self.setRange(root, range_val)
		self.setResolution(root, resolution_val)
		self.setFilter(root, filter_val)
		self.setTime(root, time_val)
		self.setApertureMode(root, aperture_mode)

	# dinamico in base a source, probabile switch state
	def init_trigger_base(self, event, count, ecount, delay, holdoff):
		root = InstrumentConfig.ROOT_TRIGGER
		self.setReset(root)
		self.setCount(root, count)
		self.setCount(root, ecount)
		self.setDelay(root, delay)
		self.setHoldoff(root, holdoff)


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
		if value not in InstrumentConfig.VALID_APERTURE_MODES:
			raise ValueError(
				f"Invalid aperture mode '{value}'. "
				f"Expected one of {InstrumentConfig.VALID_APERTURE_MODES}"
			)
		cmd = root + ":APER:MODE " + str(value)
		logging.info(f"[APERTURE] Sending: {cmd}")
		self.write(cmd)
		result = self.getApertureMode(root)
		logging.info(f"[APERTURE] Query result: {result}")
		return result
	
	def getTime(self, root):
		'''
		Get Nplc value for given root
		Input:
			root
		Output:
			float, set value
		'''
		return float(self.query(root+":APER?"))
	def setTime(self, root, value):
		'''
		Sets seonds value for given root.
		Input:
			root  : SCPI root string e.g. ":VOLT:DC"
			value : float between 20μ and 10. Seconds
		Output:
			float, set value as string
		'''
		if not InstrumentConfig.MIN_TIME <= float(value) <= InstrumentConfig.MAX_TIME:
			raise ValueError(
				f"TIME must be between {InstrumentConfig.MIN_TIME} "
				f"and {InstrumentConfig.MAX_TIME}, got {value}"
			)
		self.write(root + ":APER " + str(value))
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
		if value not in InstrumentConfig.IMPEDANCES_DCV_VAL:
			raise ValueError(
				f"Invalid impedance '{value}'. "
				f"Expected one of {InstrumentConfig.IMPEDANCES_DCV_VAL}"
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
			return InstrumentConfig.RANGE_MODE_AUTO_STR
		elif response == 0:
			return InstrumentConfig.RANGE_MODE_MAN_STR
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
		if value == InstrumentConfig.RANGE_MODE_AUTO_STR:
			converted_value = InstrumentConfig.RANGE_MODE_AUTO
		elif value == InstrumentConfig.RANGE_MODE_MAN_STR:
			converted_value = InstrumentConfig.RANGE_MODE_MAN
		else:
			raise ValueError(
				f"Invalid range mode '{value}'. "
				f"Expected '{InstrumentConfig.RANGE_MODE_AUTO_STR}' "
				f"or '{InstrumentConfig.RANGE_MODE_MAN_STR}'"
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
	
	def getResolution(self, root):
		'''
		Get resolution value for given root
		Input:
			root
		Output:
			int, digit count (4-8 for DC, 4-7 for AC)
		'''
		raw_resolution = float(self.query(root+":RES?"))
		return self.__anti_convert_resolution(raw_resolution)
	def setResolution(self, root, value):
		'''
		Sets resolution in digits for given root.
		Converts digit count to the resolution value the instrument expects.
		Input:
			root  : SCPI root string e.g. ":VOLT:DC"
			value : int or str, number of digits (4–8 for DC, 4–7 for AC)
		Output:
			float, set value in digits

		Example:
			setResolution(":VOLT:DC", 4) --> measures 1.2348 V  (returns 4)
			setResolution(":VOLT:DC", 6) --> measures 1.234778 V (returns 6)
		'''
		digit_value = int(value)
		is_ac = "AC" in root.upper()
		
		if is_ac:
			if digit_value not in InstrumentConfig.VALID_RESOLUTIONS_AC_DIGITS:
				raise ValueError(
					f"AC resolution must be one of {InstrumentConfig.VALID_RESOLUTIONS_AC_DIGITS}, got {digit_value}"
				)
		else:
			if digit_value not in InstrumentConfig.VALID_RESOLUTIONS_DC_DIGITS:
				raise ValueError(
					f"DC resolution must be one of {InstrumentConfig.VALID_RESOLUTIONS_DC_DIGITS}, got {digit_value}"
				)
		
		converted_resolution = self.__convert_resolution(digit_value)
		self.write(root + ":RES " + str(converted_resolution))
		set_resolution = self.getResolution(root)
		return self.__anti_convert_resolution(set_resolution)
	
	def __convert_resolution(self, value):
		return 10**(-value)

	def __anti_convert_resolution(self, value):
		# Check if value is already in digit format (4-8)
		# This handles machines that return resolution as digit count directly
		if value >= 4 and value <= 8 and value == int(value):
			return int(value)
		
		# Otherwise, convert from scientific notation (1E-4 -> 4 digits)
		formatted = f"{float(value):.17f}"
		after_decimal = formatted.split(".")[1]
		for i, digit in enumerate(after_decimal, start=1):
			if digit == '1':
				return i
			elif digit != '0':
				raise ValueError(
					f"Unexpected resolution from instrument: {value}. "
				)
		raise ValueError(
			f"No significant digit found in resolution value: {value}"
		)

	#ACI
	def getBlimit(self, root):
		return self.query(f"{root}:COUNter:BLIMit[:STATe]?")

	def setBlimit(self, root, value:bool):
		self.write(f"{root}:COUNter:BLIMit {int(value)}")
		return self.getBlimit(root)

	def getCounterCoupling(self, root):
		return self.query(f"{root}:COUNter:COUPling?")

	def setCounterCoupling(self, root, value):
		self.write(f"{root}:COUNter:COUPling {value}")
		return self.getCounterCoupling(root)

	def getGateMode(self, root):
		return self.query(f"{root}:COUNter:GATE:AUTO?")

	def setGateMode(self, root, value:bool):
		self.write(f"{root}:COUNter:GATE:AUTO {value}")
		return self.getGateMode(root)

	def getCoupling(self, root):
			return self.query(f"{root}:COUPling?")

	def setCoupling(self, root, value):
		self.write(f"{root}:COUPling {value}")

	def getFilter(self, root):
		return bool(int(self.query(f"{root}:FILTer?").strip()))

	def setFilter(self, root, value):
		self.write(f"{root}:FILTer {value}")
		return self.getFilter(root)

	def getCounterGate(self, root):
		return self.query(f"{root}:COUNter:GATE?")

	def setCounterGate(self, root, value):
		self.write(f"{root}:COUNter:GATE {value}")
		return self.getCounterGate(root)

	def getSecondary(self, root):
		return self.query(f"{root}:SECondary?")
	def setSecondary(self, root, value:str):
		self.write(f"{root}:SECondary {value}")
		return self.getSecondary(root)
	
	def getSecondaryMethod(self, root):
		return self.query(f"{root}:SECondary:METHod?")

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
		return self.query(f"{root}:BWIDth?")

	def setBwidth(self, root, value):
		self.write(f"{root}:BWIDth {value}")
		return self.getBwidth(root)

	def getCouplingSignal(self, root):
		return self.query(f"{root}:COUPling:SIGNal?")

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

	def setImmediate(self, root):
		return self.write(f"{root}")
	
	#ARM1 ARM2
	def getCount(self, root):
		return self.query(f"{root}:COUNt?")
	def setCount(self, root, value):
		self.write(f"{root}:COUNt {value}")
		return self.getCount(root)

	def getCoupling(self, root):
		return self.query(f"{root}:COUP?")
	def setCoupling(self, root, coupling:str):
		return self.write(f"{root}:COUP {coupling}")
	
	def getDelay(self, root):
		return self.query(f"{root}:DELay?")
	def setDelay(self, root, value):
		self.write(f"{root}:DELay {value}")
		return self.getDelay(root)
	
	def getDelayMode(self, root):
		return self.query(f"{root}:DELay:AUTO?")
	def setDelayMode(self, root, value:bool):
		self.write(f"{root}:DELay:AUTO {value}")
		return self.getDelay(root)
	
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

	def getFilter(self, root):
		return self.query(f"{root}:FILT?")
	def getFilter(self, root, filter:bool):
		return self.write(f"{root}:FILT {filter}")

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
	def setHoldoffAuto(self, root, value):
		self.write(f"{root}:HOLDoff:AUTO {value}")
		return self.getHoldoffAuto(root)

	def getHoldoff(self, root):
		return self.query(f"{root}:HOLDoff?")
	def setHoldoff(self, root, value):
		self.write(f"{root}:HOLDoff {value}")
		return self.getHoldoff(root)

	def setReset(self, root):
		return self.write(f"{root}:RES")
	

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

	# RESISTANCE and FRESISTANCE (only chane is mode, which has True as an extra option)
	def getWireMode(self, root):
		return self.query(f"{root}:MODE?").strip()
	def setWireMode(self, root, value):
		'''
		input: (root, NORMal || HIV || TRUE);
		Output:  NORMal|| HIV || TRUE ;
		Sets the 2-wire Ohms mode, returns the mode that has been set in machine.
		'''
		self.write(f"{root}:MODE {value}")
		return self.getWireMode(root)
	
	def getLowCurrentMode(self, root):
		return bool(int(self.query(f"{root}:LOWI?").strip()))
	def setLowCurrentMode(self, root, value):
		'''
		input: (root, 1 || 0);
		Output:  1 || 0; TO BE CHECKED
		Sets the Low current mode ON or OFF
		'''
		self.write(f"{root}:LOWI {value}")
	