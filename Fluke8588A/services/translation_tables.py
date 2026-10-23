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
	gui.AUTO: "AUTO ON",  # not sent: with range mode AUTO only RANG:AUTO is written
	"10 μA": 1e-5,
	"100 μA": 1e-4,
	"1 mA": 1e-3,
	"10 mA": 1e-2,
	"100 mA": 1e-1,
	"1 A": 1,
	"10 A": 1e1,
	"30 A": 3e1,
}

OHM_RANGE = {
	gui.AUTO: "AUTO ON",
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

OHM_MODE = {
	"2W NORMAL": scpi.OHM_MODE_NORMAL,
	"4W NORMAL": scpi.OHM_MODE_NORMAL,
	gui.OHM_MODE_4W_TRUE: scpi.OHM_MODE_TRUE,
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

# Tables addressed by name through Translator.translate()/translate_from_machine()
GUI_TO_SCPI = {
	"range_mode": RANGE_MODE,
	"aperture_mode": APERTURE_MODE,
	"dcv_range": DCV_RANGE,
	"dcv_impedance": DCV_IMPEDANCE,
	"dci_range": DCI_RANGE,
	"dcv_max_resolution": DCV_MAX_RESOLUTION,
	"dci_max_resolution": DCI_MAX_RESOLUTION,
	"ohm_range": OHM_RANGE,
	"ohm_mode": OHM_MODE,
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
_check_covers(TRIGGER_SOURCE, gui.TRIGGER_SOURCES, "TRIGGER_SOURCE")
_check_covers(TRIGGER_EXTERNAL_EDGE, gui.TRIGGER_EXTERNAL_EDGES, "TRIGGER_EXTERNAL_EDGE")
_check_covers(DCV_MAX_RESOLUTION, gui.DCV_RANGE[1:], "DCV_MAX_RESOLUTION")
_check_covers(DCV_MAX_RESOLUTION, [DCV_AUTO_REFERENCE_RANGE], "DCV_MAX_RESOLUTION")
_check_covers(DCI_MAX_RESOLUTION, gui.I_RANGE[1:], "DCI_MAX_RESOLUTION")
