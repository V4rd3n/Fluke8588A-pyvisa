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
class OhmsSettings:
    four: bool
    range_val:  str
    resolution: int
    mode:       str
    filter:     bool
    low_i:      bool
    aperture_mode: str
    time:       float

#TO DO, check the bellow
@dataclass
class TriggerBaseSettings:
    source:     str
    count:      int
    delay:      float
    delay_auto: bool
    holdoff:    float
    holdoff_auto: bool
    timer:      Optional[float]
    ext_edge:   Optional[str]
'''
@dataclass
class TriggerSettings:
    init_cont:    bool  = False
    arm_layer1:   TriggerLayerSettings = field(default_factory=TriggerLayerSettings)
    arm_layer2:   TriggerLayerSettings = field(default_factory=TriggerLayerSettings)
    trigger:      TriggerLayerSettings = field(default_factory=TriggerLayerSettings)
    holdoff:      float = 0.0
    holdoff_auto: bool  = True
    ext_edge:     str   = "NEGative"
    ext_type:     str   = "TTL"
'''