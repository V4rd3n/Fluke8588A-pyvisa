from Fluke8588A.instrument.config import InstrumentConfig
# UI display lists — what gets shown in combo boxes and spinboxes
# These are the values the user sees and selects in the interface.
# Instrument validation lives in InstrumentConfig, not here.

# Rework with new graphic handling

FUNCTIONS =     ["DCV", "DCI", "ACV", "ACI", "OHMS", "DIGITIZE"]
DCV_RANGE =     ["AUTO", "100 mV", "1 V", "10 V", "100 V", "1 kV"]
DCV_IMPEDENCE = ["AUTO", "10 MΩ", "1 MΩ"]
ACV_RANGE =     ["AUTO", "10 mV", "100 mV", "1 V", "10 V", "100 V", "1 kV"]
I_RANGE =       ["AUTO", "10 μA", "100 μA", "1 mA", "10 mA", "100 mA", "1 A", "10 A", "30 A"]

RMS_FILTER =    ["0.1Hz", "1Hz", "10Hz", "40Hz", "100Hz", "1kHz"]
ACV_COUPIMP =    ["DC, Auto", "DC, 1MΩ", "DC, 10MΩ", "AC 1MΩ", "AC 10MΩ"]
AC_SECREAD =    ["OFF", "Frequency", "Period", "Pk to Pk", "Crest factor", "Positive peak", "Negative peak"]
AC_COUNTGATE =  ["AUTO", "1ms", "10ms", "100ms", "1s"]
AC_PK2PK =      ["Measured", "Sine", "Square", "Triangle", "Truncated sine"]

EIG_DIGIT_VAL = sorted(InstrumentConfig.VALID_RESOLUTIONS_DC_DIGITS) 
SEV_DIGIT_VAL = sorted(InstrumentConfig.VALID_RESOLUTIONS_AC_DIGITS)

AUTO_FAST_VALUES = [1e-2, 1e-1, 1, 1e1, 1e2]  # values for autofast at 4,5,6,7,8 digits

OHM_MODES = ["2W NORMAL", "4W NORMAL", "4W Tru"]
OHM_RANGE = ["AUTO", "1 Ω", "10 Ω", "100 Ω", "1 kΩ", "10 kΩ", "100 kΩ", "1 MΩ", "10 MΩ", "100 MΩ", "1 GΩ"]
OHM_TRU_RANGE = ["AUTO", "1 Ω", "10 Ω", "100 Ω", "1 kΩ", "10 kΩ"]

DIGI_V_RANGE =  ["100 mV", "1 V", "10 V", "100 V", "1 kV"]
DIGI_I_RANGE =  ["10 μA", "100 μA", "1 mA", "10 mA", "100 mA", "1 A", "10 A", "30 A"]
DIGI_V_COUPIMP = ["DC, Auto", "DC, 1MΩ", "DC, 10MΩ", "AC, 1MΩ", "AC, 10MΩ"]
DIGI_I_COUPIMP = ["DC, Auto", "AC, Auto"]
DIGI_FILTER = ["OFF", "100 kHZ", "3 MHz"]

#Trigger 
TRIGGER_EVENTS = ["Bus", "External", "Hold", "Immediate", "Internal", "Line", "Manual", "Synchronous", "Timer"]

def get_functions():
    return FUNCTIONS

def get_dcv_range():
    return DCV_RANGE

def get_dci_range():
    return I_RANGE

def get_dcv_impedence():
    return DCV_IMPEDENCE

def get_acv_range():
    return ACV_RANGE

def get_rms_filter():
    return RMS_FILTER

def get_acv_coupling_impedance():
    return ACV_COUPIMP

def get_ac_secondary_reading():
    return AC_SECREAD

def get_ac_count_gate():
    return AC_COUNTGATE

def get_ac_peak_to_peak():
    return AC_PK2PK



def get_dc_digit_val():
    return EIG_DIGIT_VAL

def get_ac_digit_val():
    return SEV_DIGIT_VAL

def get_ohm_modes():
    return OHM_MODES

def get_ohm_range():
    return OHM_RANGE

def get_ohm_tru_range():
    return OHM_TRU_RANGE

def get_digi_v_range():
    return DIGI_V_RANGE

def get_digi_i_range():
    return DIGI_I_RANGE

def get_digi_v_coupling_impedance():
    return DIGI_V_COUPIMP

def get_digi_i_coupling_impedance():
    return DIGI_I_COUPIMP


def get_trigger_events():
    return TRIGGER_EVENTS