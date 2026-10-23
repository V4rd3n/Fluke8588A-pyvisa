"""
GUI -> SCPI translation tables (Presenter side).

Each table maps a label/token from data/gui_values.py to the value the
instrument expects (instrument/scpi.py). This is the only module that knows
both sides; it is used by the Translator, never directly by views or model.

Access it as a namespace:  from Fluke8588A.services import translation_tables as tables
"""
from Fluke8588A.data import gui_values as gui
from Fluke8588A.instrument import scpi

RANGE_MODE = {
	gui.RANGE_MODE_AUTO: scpi.RANGE_MODE_AUTO_STR,
	gui.RANGE_MODE_MAN: scpi.RANGE_MODE_MAN_STR,
}

APERTURE_MODE = {
	gui.APERTURE_AUTO: scpi.APERTURE_MODE_AUTO,
	gui.APERTURE_FAST: scpi.APERTURE_MODE_FAST,
	gui.APERTURE_MAN: scpi.APERTURE_MODE_MAN,
}

DCV_RANGE = {
	gui.AUTO: "AUTO",  # not sent: with range mode AUTO DCV_AUTO_REFERENCE_RANGE is written
	"100 mV": 1e-1,
	"1 V": 1,
	"10 V": 1e1,
	"100 V": 1e2,
	"1 kV": 1e3,
}

# The absolute resolution (RES) is interpreted on the range active when it is
# written, and the instrument keeps the digits when the range changes, also in
# autorange. With range mode AUTO the resolution is therefore written on this
# manual range before autorange is enabled.
DCV_AUTO_REFERENCE_RANGE = "1 kV"

DCV_IMPEDANCE = {
	gui.AUTO: "AUTO",
	"10 MΩ": "10M",
	"1 MΩ": "1M",
}

DCI_RANGE = {
	gui.AUTO: "AUTO ON",  # not sent: with range mode AUTO DCI_AUTO_REFERENCE_RANGE is written
	"10 μA": 1e-5,
	"100 μA": 1e-4,
	"1 mA": 1e-3,
	"10 mA": 1e-2,
	"100 mA": 1e-1,
	"1 A": 1,
	"10 A": 1e1,
	"30 A": 3e1,
}

# Same as DCV_AUTO_REFERENCE_RANGE
DCI_AUTO_REFERENCE_RANGE = "30 A"

ACV_RANGE = {
	gui.AUTO: "AUTO",  # not sent: with range mode AUTO ACV_AUTO_REFERENCE_RANGE is written
	"10 mV": 1e-2,
	"100 mV": 1e-1,
	"1 V": 1,
	"10 V": 1e1,
	"100 V": 1e2,
	"1 kV": 1e3,
}

# Same as DCV_AUTO_REFERENCE_RANGE
ACV_AUTO_REFERENCE_RANGE = "1 kV"

ACV_BANDWIDTH = {
	gui.ACV_BANDWIDTH_WIDE: scpi.ACV_BANDWIDTH_WIDE,
	gui.ACV_BANDWIDTH_EHF: scpi.ACV_BANDWIDTH_EHF,
}

ACV_COUPLING_IMPEDANCE = {
	"DC, Auto": scpi.AC_COUPLING_DCAUTO,
	"DC, 1MΩ": scpi.AC_COUPLING_DC1M,
	"DC, 10MΩ": scpi.AC_COUPLING_DC10M,
	"AC, 1MΩ": scpi.AC_COUPLING_AC1M,
	"AC, 10MΩ": scpi.AC_COUPLING_AC10M,
}

# ACI has the same ranges as DCI
ACI_RANGE = DCI_RANGE

# Same as DCV_AUTO_REFERENCE_RANGE
ACI_AUTO_REFERENCE_RANGE = "30 A"

ACI_SIGNAL_COUPLING = {
	gui.AC_PATH_COUPLING_AC: scpi.ACI_COUPLING_AC,
	gui.AC_PATH_COUPLING_DC: scpi.ACI_COUPLING_DC,
}

AC_RMS_FILTER = {
	"0.1Hz": 0.1,
	"1Hz": 1,
	"10Hz": 1e1,
	"40Hz": 4e1,
	"100Hz": 1e2,
	"1kHz": 1e3,
}

AC_PATH_COUPLING = {
	gui.AC_PATH_COUPLING_AC: scpi.AC_COUNTER_COUPLING_AC,
	gui.AC_PATH_COUPLING_DC: scpi.AC_COUNTER_COUPLING_DC,
}

AC_BANDWIDTH_LIMIT = {
	gui.AC_BANDWIDTH_LIMIT_OFF: 0,
	gui.AC_BANDWIDTH_LIMIT_ON: 1,
}

AC_COUNTER_GATE = {
	gui.AUTO: scpi.AC_COUNTER_GATE_AUTO,  # with AUTO only the gate auto state is written
	"1ms": 1e-3,
	"10ms": 1e-2,
	"100ms": 1e-1,
	"1s": 1,
}

AC_SECONDARY_READING = {
	"OFF": scpi.AC_SECONDARY_OFF,
	"Frequency": scpi.AC_SECONDARY_FREQUENCY,
	"Period": scpi.AC_SECONDARY_PERIOD,
	gui.AC_SECREAD_PK2PK: scpi.AC_SECONDARY_PEAK_TO_PEAK,
	"Crest factor": scpi.AC_SECONDARY_CREST_FACTOR,
	"Positive peak": scpi.AC_SECONDARY_POSITIVE_PEAK,
	"Negative peak": scpi.AC_SECONDARY_NEGATIVE_PEAK,
}

AC_PEAK_TO_PEAK = {
	"Measured": scpi.AC_PTP_MEASURED,
	"Sine": scpi.AC_PTP_SINE,
	"Square": scpi.AC_PTP_SQUARE,
	"Triangle": scpi.AC_PTP_TRIANGLE,
	"Truncated sine": scpi.AC_PTP_TRUNCATED_SINE,
}

OHM_RANGE = {
	gui.AUTO: "AUTO",  # not sent: with range mode AUTO OHM_AUTO_REFERENCE_RANGE is written
	"1 Ω": 1,
	"10 Ω": 1e1,
	"100 Ω": 1e2,
	"1 kΩ": 1e3,
	"10 kΩ": 1e4,
	"100 kΩ": 1e5,
	"1 MΩ": 1e6,
	"10 MΩ": 1e7,
	"100 MΩ": 1e8,
	"1 GΩ": 1e9,
}

# The ohms resolution is always written on scpi.OHM_RESOLUTION_RANGE (see
# there), so the digits are translated on this range, also with autorange
OHM_AUTO_REFERENCE_RANGE = "10 kΩ"

# Wires and ohms mode together, the model selects RES or FRES from it
OHM_MODE = {
	"2W NORMAL": scpi.OHM_2W_NORMAL,
	"4W NORMAL": scpi.OHM_4W_NORMAL,
	gui.OHM_MODE_4W_TRUE: scpi.OHM_4W_TRUE,
}

DIGI_SIGNAL = {
	gui.DIGI_SIGNAL_VOLTAGE: scpi.DIGI_VOLTAGE,
	gui.DIGI_SIGNAL_CURRENT: scpi.DIGI_CURRENT,
}

# Digitize has the DCV and DCI ranges, without autorange (AUTO is never shown)
DIGI_V_RANGE = DCV_RANGE
DIGI_I_RANGE = DCI_RANGE

# Same values as ACV
DIGI_V_COUPLING_IMPEDANCE = ACV_COUPLING_IMPEDANCE

DIGI_I_COUPLING_IMPEDANCE = {
	"DC, Auto": scpi.ACI_COUPLING_DC,
	"AC, Auto": scpi.ACI_COUPLING_AC,
}

DIGI_FILTER = {
	"OFF": scpi.DIGI_FILTER_OFF,
	"100 kHz": scpi.DIGI_FILTER_100K,
	"3 MHz": scpi.DIGI_FILTER_3M,
}

TRIGGER_SOURCE = {
	"Bus": scpi.TRIGGER_SOURCE_BUS,
	gui.TRIGGER_SOURCE_EXTERNAL: scpi.TRIGGER_SOURCE_EXTERNAL,
	"Hold": scpi.TRIGGER_SOURCE_HOLD,
	"Immediate": scpi.TRIGGER_SOURCE_IMMEDIATE,
	gui.TRIGGER_SOURCE_INTERNAL: scpi.TRIGGER_SOURCE_INTERNAL,
	"Line": scpi.TRIGGER_SOURCE_LINE,
	"Manual": scpi.TRIGGER_SOURCE_MANUAL,
	"Synchronous": scpi.TRIGGER_SOURCE_SYNCHRONOUS,
	gui.TRIGGER_SOURCE_TIMER: scpi.TRIGGER_SOURCE_TIMER,
}

TRIGGER_EXTERNAL_EDGE = {
	"TTL Negative": scpi.TRIGGER_EXT_NEG_TTL,
	"TTL Positive": scpi.TRIGGER_EXT_POS_TTL,
	"Bipolar Negative": scpi.TRIGGER_EXT_NEG_BIPOLAR,
	"Bipolar Positive": scpi.TRIGGER_EXT_POS_BIPOLAR,
}

# Absolute resolution, in SI units (V, A), at the maximum displayed digits
# (gui.*_RESOLUTION_DIGITS[1]) per range label. Fewer digits mean a coarser
# resolution, one decade per digit (see Translator.translate_resolution).
DCV_MAX_RESOLUTION = {
	"100 mV": 1e-9, "1 V": 1e-8, "10 V": 1e-7, "100 V": 1e-6, "1 kV": 1e-5,
}
DCI_MAX_RESOLUTION = {
	"10 μA": 1e-12, "100 μA": 1e-11, "1 mA": 1e-10, "10 mA": 1e-9,
	"100 mA": 1e-8, "1 A": 1e-7, "10 A": 1e-6, "30 A": 1e-6,
}
# Same in Wideband and Extended HF
ACV_MAX_RESOLUTION = {
	"10 mV": 1e-9, "100 mV": 1e-8, "1 V": 1e-7, "10 V": 1e-6, "100 V": 1e-5, "1 kV": 1e-4,
}
# Same as DCI (checked on the instrument)
ACI_MAX_RESOLUTION = DCI_MAX_RESOLUTION
# Range * 1E-8 on every range, same in 2W, 4W and TRUE (checked on the instrument)
OHM_MAX_RESOLUTION = {
	"1 Ω": 1e-8, "10 Ω": 1e-7, "100 Ω": 1e-6, "1 kΩ": 1e-5, "10 kΩ": 1e-4,
	"100 kΩ": 1e-3, "1 MΩ": 1e-2, "10 MΩ": 1e-1, "100 MΩ": 1, "1 GΩ": 1e1,
}

# Tables addressed by name through Translator.translate()/translate_from_machine()
GUI_TO_SCPI = {
	"range_mode": RANGE_MODE,
	"aperture_mode": APERTURE_MODE,
	"dcv_range": DCV_RANGE,
	"dcv_impedance": DCV_IMPEDANCE,
	"dci_range": DCI_RANGE,
	"dcv_max_resolution": DCV_MAX_RESOLUTION,
	"dci_max_resolution": DCI_MAX_RESOLUTION,
	"acv_range": ACV_RANGE,
	"acv_max_resolution": ACV_MAX_RESOLUTION,
	"acv_bandwidth": ACV_BANDWIDTH,
	"acv_coupling_impedance": ACV_COUPLING_IMPEDANCE,
	"aci_range": ACI_RANGE,
	"aci_max_resolution": ACI_MAX_RESOLUTION,
	"aci_signal_coupling": ACI_SIGNAL_COUPLING,
	"ac_rms_filter": AC_RMS_FILTER,
	"ac_path_coupling": AC_PATH_COUPLING,
	"ac_bandwidth_limit": AC_BANDWIDTH_LIMIT,
	"ac_counter_gate": AC_COUNTER_GATE,
	"ac_secondary_reading": AC_SECONDARY_READING,
	"ac_peak_to_peak": AC_PEAK_TO_PEAK,
	"ohm_range": OHM_RANGE,
	"ohm_mode": OHM_MODE,
	"ohm_max_resolution": OHM_MAX_RESOLUTION,
	"digi_signal": DIGI_SIGNAL,
	"digi_v_range": DIGI_V_RANGE,
	"digi_i_range": DIGI_I_RANGE,
	"digi_v_coupling_impedance": DIGI_V_COUPLING_IMPEDANCE,
	"digi_i_coupling_impedance": DIGI_I_COUPLING_IMPEDANCE,
	"digi_filter": DIGI_FILTER,
	"trigger_source": TRIGGER_SOURCE,
	"trigger_external_edge": TRIGGER_EXTERNAL_EDGE,
}


def _check_covers(table: dict, labels, name: str) -> None:
	missing = [label for label in labels if label not in table]
	if missing:
		raise RuntimeError(f"translation table {name} has no entry for GUI values {missing}")


# Every value the GUI can show must be translatable
_check_covers(DCV_RANGE, gui.DCV_RANGE, "DCV_RANGE")
_check_covers(DCV_IMPEDANCE, gui.DCV_IMPEDANCE, "DCV_IMPEDANCE")
_check_covers(DCI_RANGE, gui.I_RANGE, "DCI_RANGE")
_check_covers(OHM_RANGE, gui.OHM_RANGE + gui.OHM_TRU_RANGE, "OHM_RANGE")
_check_covers(OHM_MODE, gui.OHM_MODES, "OHM_MODE")
_check_covers(OHM_MAX_RESOLUTION, gui.OHM_RANGE[1:], "OHM_MAX_RESOLUTION")
if OHM_RANGE[OHM_AUTO_REFERENCE_RANGE] != scpi.OHM_RESOLUTION_RANGE:
	raise RuntimeError("OHM_AUTO_REFERENCE_RANGE must be scpi.OHM_RESOLUTION_RANGE")
_check_covers(TRIGGER_SOURCE, gui.TRIGGER_SOURCES, "TRIGGER_SOURCE")
_check_covers(TRIGGER_EXTERNAL_EDGE, gui.TRIGGER_EXTERNAL_EDGES, "TRIGGER_EXTERNAL_EDGE")
_check_covers(DCV_MAX_RESOLUTION, gui.DCV_RANGE[1:], "DCV_MAX_RESOLUTION")
_check_covers(DCV_MAX_RESOLUTION, [DCV_AUTO_REFERENCE_RANGE], "DCV_MAX_RESOLUTION")
_check_covers(DCI_MAX_RESOLUTION, gui.I_RANGE[1:], "DCI_MAX_RESOLUTION")
_check_covers(DCI_MAX_RESOLUTION, [DCI_AUTO_REFERENCE_RANGE], "DCI_MAX_RESOLUTION")
_check_covers(ACV_RANGE, gui.ACV_RANGE, "ACV_RANGE")
_check_covers(ACV_MAX_RESOLUTION, gui.ACV_RANGE[1:], "ACV_MAX_RESOLUTION")
_check_covers(ACV_MAX_RESOLUTION, [ACV_AUTO_REFERENCE_RANGE], "ACV_MAX_RESOLUTION")
_check_covers(ACV_COUPLING_IMPEDANCE, gui.ACV_COUPLING_IMPEDANCE, "ACV_COUPLING_IMPEDANCE")
_check_covers(ACI_RANGE, gui.I_RANGE, "ACI_RANGE")
_check_covers(ACI_MAX_RESOLUTION, gui.I_RANGE[1:], "ACI_MAX_RESOLUTION")
_check_covers(ACI_MAX_RESOLUTION, [ACI_AUTO_REFERENCE_RANGE], "ACI_MAX_RESOLUTION")
_check_covers(AC_RMS_FILTER,gui.RMS_FILTER, "AC_RMS_FILTER")
_check_covers(AC_COUNTER_GATE, gui.AC_COUNTER_GATE, "AC_COUNTER_GATE")
_check_covers(AC_SECONDARY_READING, gui.AC_SECONDARY_READING, "AC_SECONDARY_READING")
_check_covers(AC_PEAK_TO_PEAK, gui.AC_PEAK_TO_PEAK, "AC_PEAK_TO_PEAK")
_check_covers(DIGI_SIGNAL, [gui.DIGI_SIGNAL_VOLTAGE, gui.DIGI_SIGNAL_CURRENT], "DIGI_SIGNAL")
_check_covers(DIGI_V_RANGE, gui.DIGI_V_RANGE, "DIGI_V_RANGE")
_check_covers(DIGI_I_RANGE, gui.DIGI_I_RANGE, "DIGI_I_RANGE")
_check_covers(DIGI_V_COUPLING_IMPEDANCE, gui.DIGI_V_COUPLING_IMPEDANCE, "DIGI_V_COUPLING_IMPEDANCE")
_check_covers(DIGI_I_COUPLING_IMPEDANCE, gui.DIGI_I_COUPLING_IMPEDANCE, "DIGI_I_COUPLING_IMPEDANCE")
_check_covers(DIGI_FILTER, gui.DIGI_FILTER, "DIGI_FILTER")
