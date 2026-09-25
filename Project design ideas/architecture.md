# Fluke8588A — Architecture Diagrams

## Module / File Structure

```mermaid
graph TD
    main["main.py\nENTRY"]

    subgraph controllers ["src/Fluke8588A/controllers/"]
        app_ctrl["app_controller.py\nAppController"]
        instr_ctrl["instrument_controller.py\nInstrumentController"]
        meas_ctrl["measurment_controller.py\nReadingThread"]
    end

    subgraph views ["src/Fluke8588A/views/"]
        main_win["main_window.py\nMainWindow"]
        setup_dlg["dc_measurment_setup.py\nDcMeasurmentWindow"]
        plot["plot_widget.py\nDmmPlotWidget"]
    end

    subgraph ui_files ["src/Fluke8588A/ui/  (Qt Designer files)"]
        mainwindow_ui["mainwindow.ui"]
        meassetup_ui["dc_measurment_setup.ui"]
        trigger_ui["trigger.ui"]
    end

    subgraph hardware ["src/Fluke8588A/instrument/"]
        fluke["Fluke8588A.py\nFluke8588A"]
        config["config.py\nInstrumentConfig"]
    end

    subgraph services ["src/Fluke8588A/services/"]
        translator["translator.py\nTranslator"]
    end

    subgraph data ["src/Fluke8588A/data/"]
        settings["settings.py\nMeasurement settings"]
        sbv["spin_box_values.py\nSpinBoxValues"]
    end

    main --> app_ctrl
    app_ctrl --> instr_ctrl
    app_ctrl --> meas_ctrl
    app_ctrl --> main_win
    instr_ctrl --> fluke
    instr_ctrl --> config
    meas_ctrl --> instr_ctrl
    meas_ctrl --> sbv
    meas_ctrl --> setup_dlg
    main_win --> sbv
    fluke --> config
    sbv --> config
    app_ctrl --> translator
    app_ctrl --> settings
    main_win --> settings
    main_win --> plot

    main_win -- "uic.loadUi()" --> mainwindow_ui
    setup_dlg -- "uic.loadUi()" --> meassetup_ui
```

---

## Class Diagram

```mermaid
classDiagram

    class Fluke8588A {
        -_instr : Resource
        -_address : int
        -__connect(address)
        +identify() str
        +write(text)
        +query(text) str
        +read() str
        +reset()
        +close()
        +init_dcv(range_val, resolution, zin, nplc)
        +getRange(root) str
        +setRange(root, value) str
        +getResolution(root) str
        +setResolution(root, value) int
        +getNplc(root) str
        +setNplc(root, value) str
        +getImp(root) str
        +setImpedence(root, value) str
        +getRangeMode(root) str
        +setRangeMode(root, value) str
        +getApertureMode(root) str
        +setApertureMode(root, value) str
    }

    class InstrumentController {
        -_dmm : Fluke8588A
        -_state : InstrumentState
        -_address : int
        +connect(address)
        +disconnect()
        +is_connected() bool
        +dmm() Fluke8588A
        <<signal>> connected(idn str)
        <<signal>> disconnected()
        <<signal>> error(msg str)
    }

    class MeasurementController {
        -_instr_ctrl : InstrumentController
        -_mode : str
        -_config : MeasConfig
        +set_mode(mode)
        +read() str
        +apply_config(cfg MeasConfig)
        +get_mode() str
        <<signal>> reading_ready(value str)
        <<signal>> mode_changed(mode str)
        <<signal>> config_applied(cfg MeasConfig)
    }

    class AppController {
        -_instr_ctrl : InstrumentController
        -_meas_ctrl : MeasurementController
        -_view : MainWindow
        +__init__()
        -_connect_signals()
        -_on_init_clicked()
        -_on_read_clicked()
        -_on_mode_changed(mode)
        -_on_config_changed(cfg)
    }

    class MainWindow {
        +init_btn : QPushButton
        +read_btn : QPushButton
        +mode_combo : QComboBox
        +status_lbl : QLabel
        +measure_lbl : QLabel
        +gpib_spin : QSpinBox
        +show()
        +set_status(msg)
        +set_reading(val)
        +set_mode_visible(mode)
        <<signal>> init_requested(addr int)
        <<signal>> read_requested()
        <<signal>> mode_selected(mode str)
    }

    class SetupDialog {
        +nplc : float
        +time : float
        +measure_mode : str
        +exec() bool
        -_read_widgets()
    }

    class MeasConfig {
        <<dataclass>>
        +mode : str
        +range_val : str
        +resolution : int
        +nplc : float
        +zin : str
        +from_widgets(win)$ MeasConfig
    }

    class InstrumentState {
        <<enumeration>>
        DISCONNECTED
        CONNECTING
        CONNECTED
        ERROR
    }

    class InstrumentConfig {
        <<class>>
        DEFAULT_ADDRESS$ = 9
        TIMEOUT_MS$ = 10000
        PLC_MAX$ = 500
        NPLC_MIN$ = 0.001
        GPIB_PREFIX$ = GPIB0..
        GPIB_SUFFIX$ = ..INSTR
        ROOT_DCV$ = :VOLT:DC
        ROOT_DCI$ = :CURR:DC
        RANGE_MODE_AUTO$ = 1
        RANGE_MODE_MAN$ = 0
        RANGE_MODE_AUTO_STR$ = AUTO
        RANGE_MODE_MAN_STR$ = MAN
        VALID_APERTURE_MODES$ = AUTO FAST MAN
        VALID_IMPEDANCES_DCV$ = AUTO 1M 10M
        VALID_RESOLUTIONS_DC$ = 1e-4..1e-8
        VALID_RESOLUTIONS_AC$ = 1e-4..1e-7
        VALID_RESOLUTIONS_DC_DIGITS$ = 4..8
        VALID_RESOLUTIONS_AC_DIGITS$ = 4..7
    }

    class SpinBoxValues {
        <<module>>
        FUNCTIONS$
        DCV_RANGE$
        DCV_RANGE_VAL$
        DCI_RANGE$
        DCI_RANGE_VAL$
        DCV_IMPEDENCE$
        DC_DIGIT_VAL$
        AC_DIGIT_VAL$
        AUTO_FAST_VALUES$
        +get_functions() list
        +get_dcv_range() list
        +get_dci_range() list
        +get_dcv_zin() list
        +get_dcv_range_val(value) float
        +get_dci_range_val(value) float
        +get_dc_digit_val() list
        +get_ac_digit_val() list
    }

    AppController *-- InstrumentController : owns
    AppController *-- MeasurementController : owns
    AppController *-- MainWindow : owns
    InstrumentController *-- Fluke8588A : owns
    InstrumentController --> InstrumentState : uses
    InstrumentController --> InstrumentConfig : uses
    MeasurementController --> InstrumentController : uses
    MeasurementController --> MeasConfig : uses
    MeasurementController --> SetupDialog : opens
    MeasurementController --> SpinBoxValues : uses
    AppController --> MeasConfig : creates
    Fluke8588A --> InstrumentConfig : uses
    MainWindow --> SpinBoxValues : uses
    SpinBoxValues --> InstrumentConfig : uses
```