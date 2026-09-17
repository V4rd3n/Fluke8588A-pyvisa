from dataclasses import dataclass, field

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
class TriggerLayerSettings:
    source:     str   = "IMMediate"
    count:      int   = 1
    delay:      float = 0.0
    delay_auto: bool  = True
    timer:      float = 0.002   #2ms default, only used when source=TIMer

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