from dataclasses import dataclass, field
from typing import Optional

@dataclass
class DcvSettings:
    range_mode: str
    range_val:  str
    resolution: int
    zin:        str
    aperture_mode: str
    time:       float 

@dataclass
class DciSettings:
    range_mode: str
    range_val:  str
    resolution: int
    aperture_mode: str
    time:       float 

@dataclass
class AcvSettings:
    range_mode: str
    range_val: str
    resolution: int
    rms_filter: str
    coupling_impedance: str
    secondary_reading: str
    frequency_path_coupling: str
    frequency_path_bandwidth_limit: str
    counter_gate: str
    bandwidth: str
    peak_to_peak: str

@dataclass
class AciSettings:
    range_mode: str
    range_val: str
    resolution: int
    rms_filter: str
    signal_path_coupling: str
    secondary_reading: str
    frequency_path_coupling: str
    frequency_path_bandwidth_limit: str
    counter_gate: str
    peak_to_peak: str

@dataclass
class OhmsSettings:
    range_mode: str
    range_val:  str
    resolution: int
    mode:       str  # wires and ohms mode together, e.g. "2W NORMAL", "4W Tru"
    filter:     bool
    low_current: bool
    aperture_mode: str
    time:       float

@dataclass
class DigitizeSettings:
    signal:     str  # voltage or current, the model selects :DIG:VOLT or :DIG:CURR from it
    range_val:  str
    coupling_impedance: str  # with current only the coupling, the impedance is always auto
    filter:     str
    aperture:   float  # seconds, shared by voltage and current

#TO DO, implement a TriggerSettings
@dataclass
class TriggerBaseSettings:
    source:     str
    count:      int
    ecount:     int
    delay:      float
    delay_auto: bool
    holdoff:    float
    holdoff_auto: bool
    timer:      Optional[float]
    ext_edge:   Optional[str]
    sig_coupling: Optional[str]
    sig_slope:  Optional[str]
    sig_level:  Optional[int]
    sig_filter: Optional[bool]
