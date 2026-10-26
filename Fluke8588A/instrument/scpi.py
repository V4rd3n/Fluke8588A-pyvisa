"""
SCPI knowledge of the Fluke 8588A (Model layer).

Command roots, connection parameters, instrument limits and the values the
instrument accepts. Only the model (Fluke8588A, InstrumentController) and the
translation layer import this module: views never do.

Access it as a namespace:  from Fluke8588A.instrument import scpi  ->  scpi.ROOT_DCV
"""
from datetime import datetime

# Communication timeouts; the address is chosen from the VISA resource scan
TIMEOUT_MS = 10_000
SCAN_TIMEOUT_MS = 2_000

# Upper bound on :SYST:ERR? reads when emptying the error queue
ERROR_QUEUE_MAX_READS = 20

# Aperture limits: the maximum is a time, so the maximum NPLC depends on the
# line frequency (APERTURE_TIME_MAX * frequency, e.g. 500 at 50 Hz, 600 at 60 Hz)
APERTURE_TIME_MAX = 10.0  # seconds
NPLC_MIN = 0.001

# Function roots
ROOT_DCV = ":VOLT:DC"
ROOT_DCI = ":CURR:DC"
ROOT_ACV = ":VOLT:AC"
ROOT_ACI = ":CURR:AC"
# Short forms: select_function compares the root with FUNC?, which answers "RES"/"FRES"
ROOT_RESISTANCE = ":RES"
ROOT_FRESISTANCE = ":FRES"
ROOT_DIGIVOLTAGE = ":DIG:VOLT"
ROOT_DIGICURRENT = ":DIG:CURR"
# Aperture and filter are shared by digitize voltage and current: they exist
# only as :DIG:APER and :DIG:FILT (:DIG:VOLT:APER is a syntax error)
ROOT_DIGITIZE = ":DIG"

# Trigger roots
ROOT_INITIATE = ":INIT"
ROOT_ARM1 = ":ARM:LAY1"
ROOT_ARM2 = ":ARM:LAY2"
ROOT_TRIGGER = ":TRIG"

# Range mode: <root>:RANG:AUTO accepts 1/0, the model exposes "AUTO"/"MAN"
RANGE_MODE_AUTO = 1
RANGE_MODE_MAN = 0
RANGE_MODE_AUTO_STR = "AUTO"
RANGE_MODE_MAN_STR = "MAN"

# Aperture modes (<root>:APER:MODE)
APERTURE_MODE_AUTO = "AUTO"
APERTURE_MODE_FAST = "FAST"
APERTURE_MODE_MAN = "MAN"
VALID_APERTURE_MODES = [APERTURE_MODE_AUTO, APERTURE_MODE_FAST, APERTURE_MODE_MAN]

# Unused: aperture used by AUTO FAST at 4, 5, 6, 7, 8 digits
# AUTO_FAST_VALUES = [1e-2, 1e-1, 1, 1e1, 1e2]

# Unused: resolution in digits accepted by the commented
# Fluke8588A.setResolution per function root (converted to 10**-digits)
# VALID_RESOLUTION_DIGITS = {
# 	ROOT_DCV: [4, 5, 6, 7, 8],
# 	ROOT_DCI: [4, 5, 6, 7],
# 	ROOT_ACV: [4, 5, 6, 7],
# 	ROOT_ACI: [4, 5, 6, 7],
# 	ROOT_RESISTANCE: [4, 5, 6, 7, 8],
# 	ROOT_FRESISTANCE: [4, 5, 6, 7, 8],
# }

# DCV input impedance (<root>:IMP)
VALID_DCV_IMPEDANCES = ["AUTO", "10M", "1M"]

# ACV operating mode (<root>:BWIDth)
ACV_BANDWIDTH_WIDE = "WIDE"
ACV_BANDWIDTH_EHF = "EHF"

# AC signal path coupling and impedance (<root>:COUPling:SIGNal); DCAuto is
# returned in its short form
AC_COUPLING_AC1M = "AC1M"
AC_COUPLING_AC10M = "AC10M"
AC_COUPLING_DC1M = "DC1M"
AC_COUPLING_DC10M = "DC10M"
AC_COUPLING_DCAUTO = "DCA"
AC_DC_SIGNAL_COUPLINGS = [AC_COUPLING_DC1M, AC_COUPLING_DC10M, AC_COUPLING_DCAUTO]

# ACI signal path coupling (<root>:COUPling), the impedance is always auto;
# ACI has no <root>:COUPling:SIGNal
ACI_COUPLING_AC = "AC"
ACI_COUPLING_DC = "DC"

# AC frequency path coupling (<root>:COUNter:COUPling)
AC_COUNTER_COUPLING_AC = "AC"
AC_COUNTER_COUPLING_DC = "DC"

# AC counter gate (<root>:COUNter:GATE): with AUTO only <root>:COUNter:GATE:AUTO
# is written, otherwise the gate in seconds
AC_COUNTER_GATE_AUTO = "AUTO"

# AC secondary reading (<root>:SECondary) and peak to peak method (<root>:SECondary:METHod)
AC_SECONDARY_OFF = "OFF"
AC_SECONDARY_FREQUENCY = "FREQ"
AC_SECONDARY_PERIOD = "PER"
AC_SECONDARY_PEAK_TO_PEAK = "PTP"
AC_SECONDARY_CREST_FACTOR = "CFAC"
AC_SECONDARY_POSITIVE_PEAK = "PPE"
AC_SECONDARY_NEGATIVE_PEAK = "NPE"
AC_PTP_MEASURED = "MEAS"
AC_PTP_SINE = "SINE"
AC_PTP_SQUARE = "SQU"
AC_PTP_TRIANGLE = "TRI"
AC_PTP_TRUNCATED_SINE = "TSIN"

# Ohms modes (<root>:MODE); TRUE exists only in 4-wire (:FRES), :RES:MODE TRUE
# is a syntax error
OHM_MODE_NORMAL = "NORM"
OHM_MODE_TRUE = "TRUE"

# Ohms measurement, wires and <root>:MODE together: the model exposes one of
# these tokens and maps it to the function root and the mode it writes
OHM_2W_NORMAL = "2W_NORM"
OHM_4W_NORMAL = "4W_NORM"
OHM_4W_TRUE = "4W_TRUE"
OHM_MEASUREMENTS = {
	OHM_2W_NORMAL: (ROOT_RESISTANCE, OHM_MODE_NORMAL),
	OHM_4W_NORMAL: (ROOT_FRESISTANCE, OHM_MODE_NORMAL),
	OHM_4W_TRUE: (ROOT_FRESISTANCE, OHM_MODE_TRUE),
}

# Range (ohms) on which the ohms resolution is written. RES is kept in digits
# when the range changes, while a write is refused above 1E+3 ohms (e.g. 4
# digits on 100 MOhm): written here, every digit count reaches every range.
# 10 kOhm is valid in every mode (TRUE stops at 10 kOhm) with 4 to 8 digits
OHM_RESOLUTION_RANGE = 1e4

# Digitize signal: the model exposes one of these tokens and maps it to the
# function root. Digitize has no autorange and no resolution
DIGI_VOLTAGE = "VOLT"
DIGI_CURRENT = "CURR"
DIGI_MEASUREMENTS = {
	DIGI_VOLTAGE: ROOT_DIGIVOLTAGE,
	DIGI_CURRENT: ROOT_DIGICURRENT,
}

# Digitize coupling: voltage uses <root>:COUPling:SIGNal with the AC_COUPLING_*
# values, current uses <root>:COUPling with the ACI_COUPLING_* values (the
# impedance is always auto, :DIG:CURR:COUP:SIGN is a syntax error)

# Digitize low pass filter (:DIG:FILTer); 100 kHz is returned as 100K, which
# is also accepted on write
DIGI_FILTER_OFF = "OFF"
DIGI_FILTER_100K = "100K"
DIGI_FILTER_3M = "3MHZ"

# Digitize aperture (:DIG:APERture) in seconds, out of range is -222
DIGI_APERTURE_MIN = 0.0
DIGI_APERTURE_MAX = 3e-3

# Trigger sources (<trigger root>:SOURce)
TRIGGER_SOURCE_BUS = "BUS"
TRIGGER_SOURCE_EXTERNAL = "EXTernal"
TRIGGER_SOURCE_HOLD = "HOLD"
TRIGGER_SOURCE_IMMEDIATE = "IMMediate"
TRIGGER_SOURCE_INTERNAL = "INTernal"
TRIGGER_SOURCE_LINE = "LINE"
TRIGGER_SOURCE_MANUAL = "MANual"
TRIGGER_SOURCE_SYNCHRONOUS = "SYNChronous"
TRIGGER_SOURCE_TIMER = "TIMer"
TRIGGER_SOURCES = [
    TRIGGER_SOURCE_BUS, TRIGGER_SOURCE_EXTERNAL, TRIGGER_SOURCE_HOLD,
    TRIGGER_SOURCE_IMMEDIATE, TRIGGER_SOURCE_INTERNAL, TRIGGER_SOURCE_LINE,
    TRIGGER_SOURCE_MANUAL, TRIGGER_SOURCE_SYNCHRONOUS, TRIGGER_SOURCE_TIMER,
]

# External trigger edges (<trigger root>:EXTernal)
TRIGGER_EXT_NEG_TTL = "NEGative,TTL"
TRIGGER_EXT_POS_TTL = "POSitive,TTL"
TRIGGER_EXT_NEG_BIPOLAR = "NEGative,BIPolar"
TRIGGER_EXT_POS_BIPOLAR = "POSitive,BIPolar"
TRIGGER_EXTERNAL_EDGES = [
    TRIGGER_EXT_NEG_TTL, TRIGGER_EXT_POS_TTL, TRIGGER_EXT_NEG_BIPOLAR, TRIGGER_EXT_POS_BIPOLAR,
]

# Initiate layer mode. EPOCH is not a SCPI token: Epoch mode is
# :INIT:CONT OFF plus :INIT:EPOC:STAR and :INIT:EPOC:STOP
INITIATE_CONTINUOUS_ON = "ON"
INITIATE_CONTINUOUS_OFF = "OFF"
INITIATE_EPOCH = "EPOCH"

# :INIT:EPOC:STAR/:STOP date format, <yyyy,mm,dd,hh,mm,ss>
EPOCH_FORMAT = "%Y,%m,%d,%H,%M,%S"
# An Epoch cannot be cleared (NONE is -102, *RST and :TRIG:RESet keep it):
# dates in the past are ignored, so this one disables it
EPOCH_DISABLED = datetime(2000, 1, 1)

# Internal trigger signal coupling (<trigger root>:COUP) and slope
# (<trigger root>:SLOPe): the GUI values are sent as they are, these lists
# are used only to read them back
TRIGGER_COUPLINGS = ["DC", "AC"]
TRIGGER_SLOPES = ["POS", "NEG"]
