"""
Default settings shown by the GUI at startup (GUI format).

The instrument is reset on connection, so these are the values the presenter
pushes into the views and uses as its initial state. Each function returns a
new instance, because the presenter mutates its settings objects.

Access it as a namespace:  from Fluke8588A.data import defaults  ->  defaults.dcv_settings()
"""
from Fluke8588A.data.settings import (
	AciSettings,
	AcvSettings,
	DciSettings,
	DcvSettings,
	DigitizeSettings,
	OhmsSettings,
	TriggerBaseSettings,
)


def dcv_settings() -> DcvSettings:
	return DcvSettings(
		range_mode="MAN",
		range_val="1 kV",
		resolution=7,
		zin="AUTO",
		aperture_mode="AUTO",
		time=1.0,
	)


def dci_settings() -> DciSettings:
	return DciSettings(
		range_mode="MAN",
		range_val="30 A",
		resolution=7,
		aperture_mode="AUTO",
		time=1.0,
	)


def acv_settings() -> AcvSettings:
	return AcvSettings(
		range_mode="MAN",
		range_val="1 kV",
		resolution=6,
		rms_filter="40Hz",
		coupling_impedance="AC, 1MΩ",
		secondary_reading="Frequency",
		frequency_path_coupling="AC",
		frequency_path_bandwidth_limit="OFF",
		counter_gate="AUTO",
		bandwidth="Wideband",
		peak_to_peak="Measured",
	)


def aci_settings() -> AciSettings:
	return AciSettings(
		range_mode="MAN",
		range_val="30 A",
		resolution=6,
		rms_filter="40Hz",
		signal_path_coupling="AC",
		secondary_reading="Frequency",
		frequency_path_coupling="AC",
		frequency_path_bandwidth_limit="OFF",
		counter_gate="AUTO",
		peak_to_peak="Measured",
	)


def ohms_settings() -> OhmsSettings:
	return OhmsSettings(
		range_mode="MAN",
		range_val="10 kΩ",
		resolution=7,
		mode="2W NORMAL",
		filter=False,
		low_current=False,
		aperture_mode="AUTO",
		time=1.0,
	)


def digitize_settings() -> DigitizeSettings:
	return DigitizeSettings(
		signal="Tension",
		range_val="1 kV",
		coupling_impedance="DC, Auto",
		filter="3 MHz",
		aperture=0.0,
	)


def trigger_base_settings() -> TriggerBaseSettings:
	return TriggerBaseSettings(
		source="Immediate",
		count=1,
		ecount=1,
		delay=0.0,
		delay_auto=True,
		holdoff=0.0,
		holdoff_auto=True,
		timer=None,
		ext_edge=None,
		sig_coupling=None,
		sig_slope=None,
		sig_level=None,
		sig_filter=None,
	)
