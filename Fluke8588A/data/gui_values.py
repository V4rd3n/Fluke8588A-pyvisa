"""
Values shown by the GUI (View layer).

Combo box items, spin box ranges and the labels/tokens the views put in the
settings dataclasses. Nothing here knows SCPI: the mapping to instrument values
lives in services/translation_tables.py.

Access it as a namespace:  from Fluke8588A.data import gui_values  ->  gui_values.DCV_RANGE
"""

# Tokens used by the views in the settings dataclasses
AUTO = "AUTO"
RANGE_MODE_AUTO = "AUTO"
RANGE_MODE_MAN = "MAN"
APERTURE_AUTO = "AUTO"
APERTURE_FAST = "FAST"
APERTURE_MAN = "MAN"

# Function selector
FUNCTIONS = ["DCV", "DCI", "ACV", "ACI", "OHMS", "DIGITIZE"]

# Resolution spin boxes (min, max) in displayed digits
DCV_RESOLUTION_DIGITS = (4, 8)
DCI_RESOLUTION_DIGITS = (4, 7)
AC_RESOLUTION_DIGITS = (4, 7)
OHMS_RESOLUTION_DIGITS = (4, 8)

# Aperture spin boxes; ranges are set at connection from the line frequency
APERTURE_TIME_DECIMALS = 6  # the minimum time, NPLC_MIN / line frequency, is ~2e-5 s
APERTURE_PLC_DECIMALS = 3
# APERTURE_STEP = 0.01  # unused, the spin box step comes from the .ui

# DCV
DCV_RANGE = [AUTO, "100 mV", "1 V", "10 V", "100 V", "1 kV"]
DCV_IMPEDANCE = [AUTO, "10 MΩ", "1 MΩ"]

# DCI / ACI
I_RANGE = [AUTO, "10 μA", "100 μA", "1 mA", "10 mA", "100 mA", "1 A", "10 A", "30 A"]

# ACV / ACI
ACV_RANGE = [AUTO, "10 mV", "100 mV", "1 V", "10 V", "100 V", "1 kV"]
RMS_FILTER = ["0.1Hz", "1Hz", "10Hz", "40Hz", "100Hz", "1kHz"]
ACV_COUPLING_IMPEDANCE = ["DC, Auto", "DC, 1MΩ", "DC, 10MΩ", "AC, 1MΩ", "AC, 10MΩ"]
ACV_BANDWIDTH_WIDE = "Wideband"
ACV_BANDWIDTH_EHF = "Extended HF"
AC_PATH_COUPLING_AC = "AC"
AC_PATH_COUPLING_DC = "DC"
AC_BANDWIDTH_LIMIT_OFF = "OFF"
AC_BANDWIDTH_LIMIT_ON = "ON"
AC_SECREAD_PK2PK = "Pk to Pk"
AC_SECONDARY_READING = ["OFF", "Frequency", "Period", AC_SECREAD_PK2PK, "Crest factor", "Positive peak", "Negative peak"]
AC_COUNTER_GATE = [AUTO, "1ms", "10ms", "100ms", "1s"]
AC_PEAK_TO_PEAK = ["Measured", "Sine", "Square", "Triangle", "Truncated sine"]

# OHMS
OHM_MODE_4W_TRUE = "4W Tru"
OHM_MODES = ["2W NORMAL", "4W NORMAL", OHM_MODE_4W_TRUE]
OHM_RANGE = [AUTO, "1 Ω", "10 Ω", "100 Ω", "1 kΩ", "10 kΩ", "100 kΩ", "1 MΩ", "10 MΩ", "100 MΩ", "1 GΩ"]
OHM_TRU_RANGE = [AUTO, "1 Ω", "10 Ω", "100 Ω", "1 kΩ", "10 kΩ"]

# DIGITIZE (no autorange)
DIGI_SIGNAL_VOLTAGE = "Tension"
DIGI_SIGNAL_CURRENT = "Current"
DIGI_V_RANGE = ["100 mV", "1 V", "10 V", "100 V", "1 kV"]
DIGI_I_RANGE = ["10 μA", "100 μA", "1 mA", "10 mA", "100 mA", "1 A", "10 A", "30 A"]
DIGI_V_COUPLING_IMPEDANCE = ["DC, Auto", "DC, 1MΩ", "DC, 10MΩ", "AC, 1MΩ", "AC, 10MΩ"]
DIGI_I_COUPLING_IMPEDANCE = ["DC, Auto", "AC, Auto"]
# *RST values, selected when the signal changes and the current item is not in the new list
DIGI_V_DEFAULT_RANGE = "1 kV"
DIGI_I_DEFAULT_RANGE = "30 A"
DIGI_DEFAULT_COUPLING_IMPEDANCE = "DC, Auto"
DIGI_FILTER = ["OFF", "100 kHz", "3 MHz"]
# Aperture spin box in seconds: 200 ns steps up to 1 ms, the instrument rounds
# a value in between up to the next step
DIGI_APERTURE_RANGE = (0.0, 3e-3)
DIGI_APERTURE_DECIMALS = 7
DIGI_APERTURE_STEP = 2e-7

# Base trigger
TRIGGER_SOURCE_EXTERNAL = "External"
TRIGGER_SOURCE_INTERNAL = "Internal"
TRIGGER_SOURCE_TIMER = "Timer"
TRIGGER_SOURCES = [
	"Bus", TRIGGER_SOURCE_EXTERNAL, "Hold", "Immediate", TRIGGER_SOURCE_INTERNAL,
	"Line", "Manual", "Synchronous", TRIGGER_SOURCE_TIMER,
]
TRIGGER_EXTERNAL_EDGES = ["TTL Negative", "TTL Positive", "Bipolar Negative", "Bipolar Positive"]
TRIGGER_COUPLING_DC = "DC"
TRIGGER_COUPLING_AC = "AC"
TRIGGER_SLOPE_POS = "POS"
TRIGGER_SLOPE_NEG = "NEG"

# Base trigger spin boxes (min, max)
TRIGGER_COUNT_RANGE = (1, 1_000_000)
TRIGGER_ECOUNT_RANGE = (1, 1_000_000)
TRIGGER_DELAY_RANGE = (0.0, 999_999.0)
TRIGGER_HOLDOFF_RANGE = (0.00000003, 4_000_000.0)
TRIGGER_TIMER_RANGE = (0.0, 999_999_999.0)
TRIGGER_LEVEL_RANGE = (-1_000_000, 1_000_000)
