class InstrumentConfig:
    DEFAULT_ADDRESS = 9
    TIMEOUT_MS = 10_000
    NPLC_MAX = 500
    NPLC_MIN = 0.001  # 20 microseconds at 50Hz
    
    MAX_TIME = 10
    MIN_TIME= 0.000001  #1 micro sec

    GPIB_PREFIX = "GPIB0::"
    GPIB_SUFFIX = "::INSTR"
    ROOT_DCV = ":VOLT:DC"
    ROOT_DCI = ":CURR:DC"
    ROOT_ACI = ":CURR:AC"
    ROOT_ACV = ":VOLT:AC"
    ROOT_RESISTANCE = ":RESistance"
    ROOT_FRESISTANCE=":FRESistance"
    RANGE_MODE_AUTO = 1
    RANGE_MODE_MAN = 0
    RANGE_MODE_AUTO_STR = "AUTO"
    RANGE_MODE_MAN_STR = "MAN"
    DEFAULT_RESOLUTION=4

    # Instrument-defined valid values — used by Fluke8588A for input validation
    VALID_APERTURE_MODES = ["AUTO", "FAST", "MAN"]
    VALID_RESOLUTIONS_DC = [1e-4, 1e-5, 1e-6, 1e-7, 1e-8]
    VALID_RESOLUTIONS_DC_DIGITS = [4, 5, 6, 7, 8]
    VALID_RESOLUTIONS_AC = [1e-4, 1e-5, 1e-6, 1e-7]
    VALID_RESOLUTIONS_AC_DIGITS = [4, 5, 6, 7]

    #range values
    DCV_RANGE_VAL = ["AUTO", 1e-1, 1, 1e1, 1e2, 1e3] #CHECK IF AUTO OR AUTO ON
    DCI_RANGE_VAL = ["AUTO ON", 1e-7, 1e-6, 1e-3, 1e-2, 1e-1, 1, 1e1, 3e1]
    OHM_RANGE_VAL = ["AUTO ON", 1, 1e1, 1e2, 1e3, 1e5, 1e6, 1e7, 1e8, 1e9] 
    OHM_MODES_VAL = ["NORM", "NORM", "TRUE","HIV", "HIV"]
    IMPEDANCES_DCV_VAL = ["AUTO", "10M", "1M"]

JSON_GUI_FILE_NAME = ".gui_settings.json"
JSON_CNTRL_FILE_NAME =  ".cntrl_settings.json"