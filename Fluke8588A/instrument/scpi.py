"""
SCPI knowledge of the Fluke 8588A (Model layer).

Command roots, connection parameters, instrument limits and the values the
instrument accepts. Only the model (Fluke8588A, InstrumentController) and the
translation layer import this module: views never do.

Access it as a namespace:  from Fluke8588A.instrument import scpi  ->  scpi.ROOT_DCV
"""

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
ROOT_RESISTANCE = ":RESistance"
ROOT_FRESISTANCE = ":FRESistance"
ROOT_DIGIVOLTAGE = ":DIG:VOLT"
ROOT_DIGICURRENT = ":DIG:CURR"

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

# Aperture used by AUTO FAST at 4, 5, 6, 7, 8 digits
AUTO_FAST_VALUES = [1e-2, 1e-1, 1, 1e1, 1e2]

# Resolution in digits accepted by Fluke8588A.setResolution (converted to 10**-digits)
VALID_RESOLUTIONS_DC_DIGITS = [4, 5, 6, 7, 8]
VALID_RESOLUTIONS_AC_DIGITS = [4, 5, 6, 7]

# DCV input impedance (<root>:IMP)
VALID_DCV_IMPEDANCES = ["AUTO", "10M", "1M"]

# Ohms wire modes (<root>:MODE)
OHM_MODE_NORMAL = "NORM"
OHM_MODE_TRUE = "TRUE"

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

# External trigger edges (<trigger root>:EXTernal)
TRIGGER_EXT_NEG_TTL = "NEGative,TTL"
TRIGGER_EXT_POS_TTL = "POSitive,TTL"
TRIGGER_EXT_NEG_BIPOLAR = "NEGative,BIPolar"
TRIGGER_EXT_POS_BIPOLAR = "POSitive,BIPolar"

# Internal trigger signal coupling (<trigger root>:COUP)
TRIGGER_COUPLINGS = ["DC", "AC"]
