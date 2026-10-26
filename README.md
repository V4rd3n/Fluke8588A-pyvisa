# Fluke8588A-pyvisa
A Python library and GUI (in development for INRIM) to control the Fluke 8588A high‑precision digitizer / DMM through pyvisa.

It will work with direct ethernet, GPIB, and USB. Will try to implement remote communication.

<img width="675" height="221" alt="image" src="https://github.com/user-attachments/assets/8736ae4a-2fa0-4576-852b-eaea4142c8ef" />

# Structure
The code follows a Model-View-Presenter layout, inside the `Fluke8588A` package:
- `instrument/` (library, stand alone)
  - `Fluke8588A.py`: pyvisa driver, one `set_<function>` method per measurement function, it writes the settings, checks the error queue and reads them back
  - `scpi.py`: SCPI roots, tokens and instrument limits
- `controllers/`
  - `instrument_controller.py`: model interface between the presenter and the driver, also applies the base and advanced trigger
  - `app_controller.py`: presenter, connects the views to the instrument
  - `measurement_controller.py`: reading thread (not used yet)
- `services/`: `translator.py` and `translation_tables.py`, translate GUI values to SCPI values and back
- `data/`: settings dataclasses (`settings.py`), GUI values (`gui_values.py`) and the `*RST` defaults (`defaults.py`)
- `views/` and `ui/`: PyQt6 windows (main window, base and advanced trigger, graph) and their Qt Designer files

`main.py` starts the GUI. The `instrument` folder is enough to write your own script or interface; the GUI (in English) needs the whole package.

On connection the instrument is reset (`*RST`) and the GUI goes back to the defaults. Debug messages are logged at DEBUG level when `AppController.TEST_MODE` is True.
