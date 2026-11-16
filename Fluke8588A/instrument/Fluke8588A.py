import pyvisa
import logging
import time
from datetime import datetime
from Fluke8588A.instrument import scpi

logger = logging.getLogger(__name__)

class Fluke8588A():
	"""
	SCPI driver of the Fluke 8588A DMM over VISA.

	The connection resets the instrument (*RST). The set_<function> methods
	(set_dcv, set_acv, ...) write all the settings of a function, check the
	error queue and then read the values back once. The single-value
	setters (setX) only write: reading back is left to the caller, after
	all the writes, since a later command can change an earlier value.
	"""

	def __init__(self, address):
		logger.info('Initializing instrument Fluke 8588A')
		self.is_connected = False
		self.__connect(address)
		self._instr.timeout = scpi.TIMEOUT_MS
		self._line_frequency = None
		self.reset()
		idn_string = self.identify()
		logger.info("Instrument %s successfully initialized.", idn_string.strip())

	def __connect(self, address):
		self._rm = pyvisa.ResourceManager()
		self._instr = self._rm.open_resource(address)
		self.is_connected = True

	def identify(self):
		"""Answer of *IDN?: manufacturer, model, serial number and firmware."""
		return self.query("*IDN?")

	def get_line_frequency(self) -> float:
		"""Return the instrument power-line frequency in hertz."""
		if self._line_frequency is None:
			self._line_frequency = float(self.query(":SYST:LFR?").strip())
		return self._line_frequency

	def write(self, text):
		"""Send a command to the instrument."""
		self._instr.write(text)

	def query(self, text):
		"""Send a query and return the answer text."""
		return self._instr.query(text)

	def read(self):
		"""Take a measurement, return the readings as comma separated text."""
		# With INIT:CONT ON (also set by an Epoch) READ? fails with -214
		# "Trigger deadlock" and FETCh? keeps answering the first reading of
		# the record (-230 "Data corrupt or stale"): FNOW? takes the new ones
		if self._is_continuous():
			return self._read_continuous()
		return self.query(":READ?")

	def read_with_secondary(self):
		"""
		Take a measurement with its secondary reading (ACV/ACI frequency, period, peaks...).

		Returns:
			(primary text, secondary text). The secondary readings are as many
			as the primary ones (FETCh? 2 of the record taken by READ?).
			Secondary text is None with INIT:CONT ON: FNOW? returns the primary
			readings only and FETCh? 2 the first reading of the record.
		"""
		if self._is_continuous():
			return self._read_continuous(), None
		primary = self.query(":READ?")
		return primary, self.query(":FETCh? 2")

	def _is_continuous(self):
		return self.getContinuos(scpi.ROOT_INITIATE).strip() == "1"

	def _fetch_new_readings(self):
		"""
		Readings taken since the previous FNOW?, oldest first, removed from
		the memory. FNOW? never waits: it answers the available ones followed
		by 9.91E+37 (only 9.91E+37 when there are none).
		"""
		answer = self.query(f":FNOW? {scpi.FNOW_MAX_READINGS}")
		return [item for item in answer.strip().split(",") if float(item) < scpi.INVALID_READING]

	def _read_continuous(self):
		"""
		Readings taken since the previous call with INIT:CONT ON, comma
		separated and oldest first; waits for at least one up to the VISA timeout.
		"""
		deadline = time.monotonic() + self._instr.timeout / 1000
		while True:
			readings = self._fetch_new_readings()
			if readings:
				return ",".join(readings)
			if time.monotonic() > deadline:
				raise TimeoutError("No new reading in continuous mode")
			time.sleep(scpi.FNOW_POLL_S)

	def start_digitize(self):
		"""
		Start a digitize acquisition and return at once: READ? would block until
		the last sample, also forever when an external trigger never arrives.
		"""
		self.write("*CLS")
		self.write(":ABORt")
		self.write(":INIT")

	def is_measuring(self):
		"""True until the trigger system is back to idle, False when the acquisition has ended."""
		condition = int(float(self.query(":STAT:OPER:COND?")))
		# The bit is set when the record is complete, not while measuring (probed)
		return not condition & scpi.OPERATION_RECORD_DONE_BIT

	def abort(self):
		"""Stop the acquisition in progress, the trigger system goes back to idle."""
		self.write(":ABORt")

	def fetch_block(self, count):
		"""Comma separated readings of the record just acquired, with a timeout long enough for count readings."""
		return self._fetch_record(":FETCh?", count)

	def fetch_time_stamps(self, count):
		"""
		Comma separated time stamps (FETCh? 5) of the record just acquired, with
		time stamps ON: the first is the time from INIT to the first reading,
		then the time from the previous reading (probed in Digitize).
		"""
		return self._fetch_record(":FETCh? 5", count)

	def _fetch_record(self, command, count):
		"""Answer of a FETCh? query, with a timeout long enough for count readings."""
		timeout = self._instr.timeout
		self._instr.timeout = scpi.TIMEOUT_MS + count * scpi.DIGI_FETCH_MS_PER_READING
		try:
			return self.query(command)
		finally:
			self._instr.timeout = timeout

	def set_time_stamps(self, state):
		"""Reading time stamps ON or OFF (:SYST:TIME:TIMer), a setting shared by all the functions."""
		self.write(f":SYST:TIME:TIM {'ON' if state else 'OFF'}")

	def discard_readings(self):
		"""
		Empty the reading memory with INIT:CONT ON, so that the next read()
		returns only readings taken from now on (ABORt does not empty it).
		"""
		if not self._is_continuous():
			return
		while self._fetch_new_readings():
			pass

	def reset(self):
		"""Return the instrument to its power-on state (*RST), waiting for the end of the reset."""
		self.write("*RST")
		# Returns when the reset is complete (probed: ~0.03 s, also after power on)
		self.query("*OPC?")

	def close(self):
		"""Close the connection with the instrument."""
		self._instr.close()
		self._rm.close()
		self.is_connected = False

	def select_function(self, root):
		"""
		Select the measurement function of root (e.g. ":VOLT:DC"), only if not
		already active: selecting it again reloads its settings and can drop the
		commands that follow (seen in ACV: a RANG written right after was ignored).
		"""
		function = root[1:]
		# FUNC? omits the default :DC and the digitize default :VOLT, e.g.
		# "VOLT" for VOLT:DC and "DIG" for DIG:VOLT
		active = self.query(":FUNC?").strip().strip('"')
		if active not in (function, function.removesuffix(":DC"), function.removesuffix(":VOLT")):
			self.write(":FUNC \"" + function + "\"")

	def check_errors(self):
		"""Empty the instrument error queue, raise RuntimeError listing the queued errors if any."""
		errors = []
		for _ in range(scpi.ERROR_QUEUE_MAX_READS):
			answer = self.query(":SYST:ERR?").strip()
			if int(answer.split(",", 1)[0]) == 0:
				break
			errors.append(answer)
		if errors:
			raise RuntimeError("Instrument error: " + "; ".join(errors))

	def _write_resolution_for_autorange(self, root, range_val, resolution_val, range_mode):
		"""
		Write range, resolution and range mode in this order.

		RES is interpreted on the active range and kept in digits when the range
		changes, so it is written on the manual range range_val before
		autorange is enabled: in AUTO, range_val is the reference range.
		"""
		self.setRange(root, range_val)
		self.setResolutionValue(root, resolution_val)
		self.setRangeMode(root, range_mode)

	def set_dcv(self, range_mode, range_val, resolution_val, zin_val, aperture_mode, time_val):
		"""
		Select DC voltage and write its settings.

		Args:
			range_mode: "AUTO" or "MAN".
			range_val: manual range; with "AUTO" the range the resolution
				refers to, then autorange is enabled.
			resolution_val: absolute resolution on range_val.
			zin_val: "AUTO", "1M" or "10M".
			aperture_mode: "AUTO", "FAST" or "MAN".
			time_val: aperture in seconds, written only with "MAN".

		Returns:
			dict of the values read back from the instrument after all writes.
		"""
		root=scpi.ROOT_DCV
		self.write("*CLS")
		self.select_function(root)
		self._write_resolution_for_autorange(root, range_val, resolution_val, range_mode)
		self.setImpedance(root, zin_val)
		self.setApertureMode(root, aperture_mode)
		if aperture_mode == scpi.APERTURE_MODE_MAN:
			self.setTime(root, time_val)
		self.check_errors()
		return {
			"range_mode": self.getRangeMode(root),
			"range_val": self.getRange(root),
			"resolution": self.getResolutionValue(root),
			"zin": self.getImp(root),
			"aperture_mode": self.getApertureMode(root),
			"time": self.getTime(root),
		}

	def set_dci(self, range_mode, range_val, resolution_val, aperture_mode, time_val):
		"""
		Select DC current and write its settings.

		Args:
			range_mode: "AUTO" or "MAN".
			range_val: manual range; with "AUTO" the range the resolution
				refers to, then autorange is enabled.
			resolution_val: absolute resolution on range_val.
			aperture_mode: "AUTO", "FAST" or "MAN".
			time_val: aperture in seconds, written only with "MAN".

		Returns:
			dict of the values read back from the instrument after all writes.
		"""
		root=scpi.ROOT_DCI
		self.write("*CLS")
		self.select_function(root)
		self._write_resolution_for_autorange(root, range_val, resolution_val, range_mode)
		self.setApertureMode(root, aperture_mode)
		if aperture_mode == scpi.APERTURE_MODE_MAN:
			self.setTime(root, time_val)
		self.check_errors()
		return {
			"range_mode": self.getRangeMode(root),
			"range_val": self.getRange(root),
			"resolution": self.getResolutionValue(root),
			"aperture_mode": self.getApertureMode(root),
			"time": self.getTime(root),
		}

	def set_aci(self, range_mode, range_val, resolution_val, filter_val, coupling_signal, counter_coupling, counter_blimit, counter_gate, secondary, secondary_method):
		"""
		Select AC current and write its settings.

		Args:
			range_mode: "AUTO" or "MAN".
			range_val: manual range; with "AUTO" the range the resolution
				refers to, then autorange is enabled.
			resolution_val: absolute resolution on range_val.
			filter_val: rms filter in hertz.
			coupling_signal: "AC" or "DC", the impedance is always auto.
			counter_coupling: "AC" or "DC", written only with a dc signal path.
			counter_blimit: 0 or 1, frequency path bandwidth limit.
			counter_gate: "AUTO" or gate in seconds.
			secondary: secondary reading, e.g. "OFF", "FREQ", "PTP".
			secondary_method: peak to peak method, e.g. "MEAS", "SINE".

		Returns:
			dict of the values read back from the instrument after all writes.
		"""
		root = scpi.ROOT_ACI
		self.write("*CLS")
		self.select_function(root)
		self._write_resolution_for_autorange(root, range_val, resolution_val, range_mode)
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

	def set_acv(self, range_mode, range_val, resolution_val, bandwidth, filter_val, coupling_signal, counter_coupling, counter_blimit, counter_gate, secondary, secondary_method):
		"""
		Select AC voltage and write its settings.

		Args:
			range_mode: "AUTO" or "MAN".
			range_val: manual range; with "AUTO" the range the resolution
				refers to, then autorange is enabled.
			resolution_val: absolute resolution on range_val.
			bandwidth: "WIDE" or "EHF".
			filter_val: rms filter in hertz.
			coupling_signal: "AC1M", "AC10M", "DC1M", "DC10M" or "DCA".
			counter_coupling: "AC" or "DC", written only with a dc signal path.
			counter_blimit: 0 or 1, frequency path bandwidth limit.
			counter_gate: "AUTO" or gate in seconds.
			secondary: secondary reading, e.g. "OFF", "FREQ", "PTP".
			secondary_method: peak to peak method, e.g. "MEAS", "SINE".

		Returns:
			dict of the values read back from the instrument after all writes.
		"""
		root=scpi.ROOT_ACV
		self.write("*CLS")
		self.select_function(root)
		# Written first: the operating mode can change the other settings
		self.setBwidth(root, bandwidth)
		self._write_resolution_for_autorange(root, range_val, resolution_val, range_mode)
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
		"""
		Select 2-wire (RES) or 4-wire (FRES) ohms and write its settings.

		Args:
			measurement: a key of scpi.OHM_MEASUREMENTS, e.g. scpi.OHM_4W_TRUE.
			range_mode: "AUTO" or "MAN".
			range_val: manual range, ignored with "AUTO".
			resolution_val: absolute resolution on scpi.OHM_RESOLUTION_RANGE.
			filter_val: filter on/off (shared by RES and FRES).
			low_current: low current on/off (kept per function and mode).
			aperture_mode: "AUTO", "FAST" or "MAN".
			time_val: aperture in seconds, written only with "MAN".

		Returns:
			dict of the values read back from the instrument after all writes.
		"""
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
		"""
		Select digitize voltage or current and write its settings.

		Args:
			measurement: a key of scpi.DIGI_MEASUREMENTS, e.g. scpi.DIGI_VOLTAGE.
			range_val: range, digitize has no autorange.
			coupling: voltage "AC1M", "AC10M", "DC1M", "DC10M" or "DCA";
				current "AC" or "DC".
			filter_val: low pass filter "OFF", "100K" or "3MHZ".
			aperture: aperture in seconds, 0 to 3 ms.

		Returns:
			dict of the values read back from the instrument after all writes.
		"""
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

	# ---- Measurement settings (root of the function, e.g. ":VOLT:DC") ----

	def getApertureMode(self, root):
		"""Aperture mode: "AUTO", "FAST" or "MAN"."""
		return self.query(root+":APER:MODE?").strip()
	def setApertureMode(self, root, value):
		"""Write the aperture mode: "AUTO", "FAST" or "MAN"."""
		if value not in scpi.VALID_APERTURE_MODES:
			raise ValueError(
				f"Invalid aperture mode '{value}'. "
				f"Expected one of {scpi.VALID_APERTURE_MODES}"
			)
		cmd = root + ":APER:MODE " + str(value)
		logger.debug(f"[APERTURE] Sending: {cmd}")
		self.write(cmd)

	def getTime(self, root):
		"""Aperture in seconds."""
		return float(self.query(root+":APER?"))
	def setTime(self, root, value):
		"""Write the aperture in seconds."""
		aperture = float(value)
		# 0 s is valid on DCV/DCI; the per-function minimum (100 us on ohms) is
		# checked by the instrument, -222
		if aperture < 0:
			raise ValueError(f"Aperture value must not be negative, got {value}")
		self.write(root + ":APER " + str(aperture))

	def getImp(self, root):
		"""DCV input impedance: "AUTO", "1M" or "10M"."""
		return self.query(root+":IMP?").strip()
	def setImpedance(self, root, value):
		"""Write the DCV input impedance: "AUTO", "1M" or "10M"."""
		if value not in scpi.VALID_DCV_IMPEDANCES:
			raise ValueError(
				f"Invalid impedance '{value}'. "
				f"Expected one of {scpi.VALID_DCV_IMPEDANCES}"
			)
		self.write(root + ":IMP " + str(value))

	def getRangeMode(self, root):
		"""Range mode: "AUTO" or "MAN"."""
		response = int(float(self.query(root+":RANG:AUTO?")))
		if response != 0:
			return scpi.RANGE_MODE_AUTO_STR
		elif response == 0:
			return scpi.RANGE_MODE_MAN_STR
		else:
			raise ValueError(f"Unexpected range mode value returned by machine: {response}")
	def setRangeMode(self, root, value):
		"""Write the range mode: "AUTO" or "MAN"."""
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

	def getRange(self, root):
		"""Range in use, also in autorange."""
		return float(self.query(root+":RANG?").strip())
	def setRange(self, root, value):
		"""Write a manual range."""
		self.write(root+":RANG "+str(value))

	def setResolutionValue(self, root, value):
		"""Write the absolute resolution, interpreted on the active range."""
		resolution_value = float(value)
		if resolution_value <= 0:
			raise ValueError(f"Resolution must be positive, got {value}")
		self.write(root + ":RES " + str(resolution_value))

	def getResolutionValue(self, root):
		"""Absolute resolution on the active range."""
		return float(self.query(root + ":RES?").strip())

	# ---- AC frequency path (ACV/ACI) ----

	def getBlimit(self, root):
		return int(float(self.query(f"{root}:COUNter:BLIMit?")))

	def setBlimit(self, root, value:bool):
		self.write(f"{root}:COUNter:BLIMit {int(value)}")

	def getCounterCoupling(self, root):
		return self.query(f"{root}:COUNter:COUPling?").strip()

	def setCounterCoupling(self, root, value):
		self.write(f"{root}:COUNter:COUPling {value}")

	def getGateMode(self, root):
		return bool(int(float(self.query(f"{root}:COUNter:GATE:AUTO?"))))

	def setGateMode(self, root, value:bool):
		self.write(f"{root}:COUNter:GATE:AUTO {int(value)}")

	def getFilter(self, root):
		"""On/off filter (ohms, trigger signal), see getRmsFilter for AC."""
		return bool(int(self.query(f"{root}:FILTer?").strip()))

	def setFilter(self, root, value:bool):
		self.write(f"{root}:FILTer {int(value)}")

	# ---- Digitize (root scpi.ROOT_DIGITIZE) ----

	def getDigitizeFilter(self, root):
		return self.query(f"{root}:FILTer?").strip()

	def setDigitizeFilter(self, root, value):
		self.write(f"{root}:FILTer {value}")

	def setDigitizeAperture(self, root, value):
		"""Write the digitize aperture in seconds (not setTime: 0 is valid here)."""
		aperture = float(value)
		if not scpi.DIGI_APERTURE_MIN <= aperture <= scpi.DIGI_APERTURE_MAX:
			raise ValueError(
				f"Digitize aperture must be between {scpi.DIGI_APERTURE_MIN} "
				f"and {scpi.DIGI_APERTURE_MAX} s, got {value}"
			)
		self.write(f"{root}:APERture {aperture}")

	# ---- AC rms filter, counter gate and secondary reading (ACV/ACI) ----

	def getRmsFilter(self, root):
		"""AC rms filter in hertz."""
		return float(self.query(f"{root}:FILTer?"))

	def setRmsFilter(self, root, value):
		"""
		Write the AC rms filter in hertz (0.1, 1, 10, 40, 100, 1000): unlike
		setFilter it is a frequency, the closest discrete setting is selected.
		"""
		self.write(f"{root}:FILTer {float(value)}")

	def getCounterGate(self, root):
		return float(self.query(f"{root}:COUNter:GATE?"))

	def setCounterGate(self, root, value):
		self.write(f"{root}:COUNter:GATE {value}")

	def getSecondary(self, root):
		return self.query(f"{root}:SECondary?").strip()
	def setSecondary(self, root, value:str):
		self.write(f"{root}:SECondary {value}")

	def getSecondaryMethod(self, root):
		return self.query(f"{root}:SECondary:METHod?").strip()

	def setSecondaryMethod(self, root, value:str):
		self.write(f"{root}:SECondary:METHod {value}")

	# ---- ACV operating mode and signal path coupling ----

	def getBwidth(self, root):
		return self.query(f"{root}:BWIDth?").strip()

	def setBwidth(self, root, value):
		self.write(f"{root}:BWIDth {value}")

	def getCouplingSignal(self, root):
		return self.query(f"{root}:COUPling:SIGNal?").strip()

	def setCouplingSignal(self, root, value):
		self.write(f"{root}:COUPling:SIGNal {value}")

	# ---- Initiate layer (root scpi.ROOT_INITIATE) ----

	def getContinuos(self, root):
		return self.query(f"{root}:CONT?")
	def setContinuos(self, root, state:bool):
		self.write(f"{root}:CONT {int(state)}")

	# Epoch dates are datetime objects, sent as <yyyy,mm,dd,hh,mm,ss>
	def setEpochStart(self, root, date:datetime):
		self.write(f"{root}:EPOC:STAR {date.strftime(scpi.EPOCH_FORMAT)}")

	def setEpochStop(self, root, date:datetime):
		self.write(f"{root}:EPOC:STOP {date.strftime(scpi.EPOCH_FORMAT)}")

	# ---- Event layers (ARM2, ARM1, TRIG) ----

	def getCount(self, root):
		return self.query(f"{root}:COUNt?")
	def setCount(self, root, value):
		self.write(f"{root}:COUNt {value}")

	# Also the ACI signal path coupling (:CURR:AC:COUP)
	def getCoupling(self, root):
		return self.query(f"{root}:COUP?").strip()
	def setCoupling(self, root, coupling:str):
		self.write(f"{root}:COUP {coupling}")

	def getDelay(self, root):
		return self.query(f"{root}:DELay?")
	def setDelay(self, root, value):
		self.write(f"{root}:DELay {value}")

	def getDelayMode(self, root):
		return self.query(f"{root}:DELay:AUTO?")
	def setDelayMode(self, root, value:bool):
		state = "ON" if value else "OFF"
		self.write(f"{root}:DELay:AUTO {state}")

	def getEcount(self, root):
		return self.query(f"{root}:ECOunt?")
	def setEcount(self, root, value):
		self.write(f"{root}:ECOunt {value}")

	def getExternal(self, root):
		return self.query(f"{root}:EXTernal?")
	def setExternal(self, root, value):
		self.write(f"{root}:EXTernal {value}")

	def getLevel(self, root):
		return self.query(f"{root}:LEVel?")
	def setLevel(self, root, value):
		self.write(f"{root}:LEVel {value}")

	def resetTrigger(self, root):
		self.write(f"{root}:RESet")

	def getSlope(self, root):
		return self.query(f"{root}:SLOPe?")
	def setSlope(self, root, value):
		self.write(f"{root}:SLOPe {value}")

	def getSource(self, root):
		return self.query(f"{root}:SOURce?")
	def setSource(self, root, value):
		self.write(f"{root}:SOURce {value}")

	def getTimer(self, root):
		return self.query(f"{root}:TIMer?")
	def setTimer(self, root, value):
		self.write(f"{root}:TIMer {value}")

	# ---- TRIG layer only ----

	def getHoldoffAuto(self, root):
		return self.query(f"{root}:HOLDoff:AUTO?")
	def setHoldoffAuto(self, root, value: bool):
		state = "ON" if value else "OFF"
		self.write(f"{root}:HOLDoff:AUTO {state}")

	def getHoldoff(self, root):
		return self.query(f"{root}:HOLDoff?")
	def setHoldoff(self, root, value):
		self.write(f"{root}:HOLDoff {value}")

	# ---- Trigger readback ----

	def __match_token(self, answer, tokens):
		"""
		The token of tokens matching an answer: the instrument answers with the
		short form (e.g. "IMM", "NEG,TTL"), mapped back to the scpi constant.
		"""
		value = answer.strip().strip('"').replace(" ", "").upper()
		for token in tokens:
			short_form = "".join(char for char in token if not char.islower())
			if value in (token.upper(), short_form.upper()):
				return token
		raise ValueError(f"Instrument returned an unsupported value: {answer!r}")

	def get_trigger_layer(self, root, holdoff=False):
		"""
		Read back one event layer.

		Args:
			root: scpi.ROOT_ARM2, scpi.ROOT_ARM1 or scpi.ROOT_TRIGGER.
			holdoff: True to read HOLDoff too, it exists only on the TRIG layer.

		Returns:
			dict, source as a scpi.TRIGGER_SOURCE_* constant, numbers parsed.
		"""
		layer = {
			"source": self.__match_token(self.getSource(root), scpi.TRIGGER_SOURCES),
			"count": int(float(self.getCount(root))),
			"ecount": int(float(self.getEcount(root))),
			"delay": float(self.getDelay(root)),
			"delay_auto": bool(int(float(self.getDelayMode(root)))),
			"timer": float(self.getTimer(root)),
		}
		if holdoff:
			layer["holdoff"] = float(self.getHoldoff(root))
			# The manual gives HOLDoff:AUTO? as 1 = ON, 2 = OFF, the instrument answers 0 for OFF
			layer["holdoff_auto"] = int(float(self.getHoldoffAuto(root))) == 1
		return layer

	def get_trigger_external(self, root):
		"""Read back the external edge as a scpi.TRIGGER_EXT_* constant."""
		return self.__match_token(self.getExternal(root), scpi.TRIGGER_EXTERNAL_EDGES)

	def get_trigger_signal(self, root):
		"""Read back the internal (signal) source settings of one layer."""
		return {
			"coupling": self.__match_token(self.getCoupling(root), scpi.TRIGGER_COUPLINGS),
			"slope": self.__match_token(self.getSlope(root), scpi.TRIGGER_SLOPES),
			"level": int(round(float(self.getLevel(root)))),
			"filter": self.getFilter(root),
		}

	# ---- Ohms (RES and FRES: same settings, FRES has the TRUE mode too) ----

	def getWireMode(self, root):
		return self.query(f"{root}:MODE?").strip()
	def setWireMode(self, root, value):
		"""Write the ohms mode: "NORM", or "TRUE" (only with :FRES)."""
		self.write(f"{root}:MODE {value}")

	def getLowCurrentMode(self, root):
		return bool(int(self.query(f"{root}:LOWI?").strip()))
	def setLowCurrentMode(self, root, value:bool):
		"""Write low current on/off, the instrument keeps it per function and per mode (NORM/TRUE)."""
		self.write(f"{root}:LOWI {int(value)}")

	# ======== Driver functions not used in current implementation ========

	# ---- Shunts (current) ----

	def init_shunt(self, root, shunt_list_index, shunt_sort=None, add_shunt_attributes=None, add_shunt_differences=None):
		"""
		Configure the shunt used by a current measurement.

		Args:
			root: SCPI root, e.g. ":CURR:AC".
			shunt_list_index: index of the shunt in the shunt list.
			shunt_sort: optional sort order ("MCURrent", "ASSet", "SERial").
			add_shunt_attributes: optional attributes of a new shunt to add.
			add_shunt_differences: optional [(frequency, difference), ...] AC-DC
				differences to add.
		"""
		if add_shunt_attributes is not None:
			self.addShunt(root, add_shunt_attributes)

		if shunt_sort is not None:
			self.setShuntSort(root, shunt_sort)

		self.pickShunt(root, shunt_list_index)

		if add_shunt_differences is not None:
			for frequency, difference in add_shunt_differences:
				self.addShuntDifference(root, frequency, difference)

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

	# ---- Initiate and event layers ----

	def getEpochStart(self, root):
		return self.query(f"{root}:EPOC:STAR?")

	def getEpochStop(self, root):
		return self.query(f"{root}:EPOC:STOP?")

	def setImmediate(self, root):
		self.write(f"{root}:IMMediate")

	def setSignal(self, root):
		self.write(f"{root}:SIGNal")
