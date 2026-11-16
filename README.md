# Fluke8588A-pyvisa
A Python library and GUI (in development for INRIM) to control the Fluke 8588A high‑precision digitizer / DMM through pyvisa.

Tested over USB and GPIB, on Windows with firmware 1.32. 

<img width="675" height="221" alt="image" src="https://github.com/user-attachments/assets/8736ae4a-2fa0-4576-852b-eaea4142c8ef" />

# Features
- Measurement functions: DCV, DCI, ACV and ACI (with a secondary reading: frequency, period, peaks, crest factor), OHMS 2-wire and 4-wire (also True Ohms), DIGITIZE voltage and current
- Base and advanced trigger (ARM2, ARM1, TRIG layers, continuous and Epoch initiate)
- Graph of the readings with statistics (mean, standard deviation, standard deviation of the mean) and Allan deviation
- DIGITIZE blocks with FFT (peak, peak frequency, THD), single or continuous, also averaged
- Every acquisition saved as CSV with a PNG of its graph, and a graph visualizer to view the files without the instrument

# Installation
Python 3.10 or later is required.

```bash
python -m pip install -r requirements.txt
```

- `pyvisa-py` is the VISA backend, not needed when NI-VISA or another VISA library is installed.
- `pyusb`, `psutil` and `zeroconf` are optional and not needed to start the program. With `pyvisa-py`, `pyusb` is used for USB connections (the libusb system library may be needed too), `psutil` and `zeroconf` to discover instruments on the network: install them separately if you use these connections.

# Usage
```bash
python main.py
```

starts the GUI: scan the VISA resources, connect, choose a function and Set it, then Start the acquisition.

```bash
python visualizer.py
```

starts the graph visualizer alone (also Utility > Graph Visualizer in the main window), to view the saved files on a PC without the instrument: it does not need pyvisa, scipy nor allantools.

On connection the instrument is reset (`*RST`) and the GUI goes back to the defaults. Debug messages are logged at DEBUG level when `AppController.TEST_MODE` is True (False by default).

# Structure
The code follows a Model-View-Presenter layout, inside the `Fluke8588A` package:
- `instrument/` (library, stand alone)
  - `Fluke8588A.py`: pyvisa driver, one `set_<function>` method per measurement function, it writes the settings, checks the error queue and reads them back; the commands not used by the GUI yet (shunts, ...) are at the end of the class
  - `scpi.py`: SCPI roots, tokens and instrument limits
- `controllers/`
  - `instrument_controller.py`: model interface between the presenter and the driver, also applies the base and advanced trigger
  - `app_controller.py`: presenter, connects the views to the instrument
  - `acquisition_controller.py`: Start/Stop of the graph window, readings, statistics, file and Allan deviation
  - `digitize_controller.py`: digitize window, block acquisition and FFT
  - `graph_visualizer_controller.py`: graph visualizer window, files saved by the program viewed without the instrument
  - `reading_thread.py`, `digitize_thread.py`, `allan_thread.py`: background threads for readings, digitize blocks and the Allan deviation
- `services/`
  - `translator.py` and `translation_tables.py`: translate GUI values to SCPI values and back
  - `statistics.py`, `allan.py`, `fft.py`: reading statistics, Allan deviation and FFT with its peak and THD
  - `measurement_file.py`: CSV files of the acquisitions in the `temp` folder (the last 10 kept) and their copies on Save
  - `measurement_reader.py`: the same files read back for the graph visualizer
  - `units.py`: units of the GUI range labels
- `data/`: settings dataclasses (`settings.py`), GUI values (`gui_values.py`) and the `*RST` defaults (`defaults.py`)
- `views/` and `ui/`: PyQt6 windows (main window, base and advanced trigger, graph, digitize, graph visualizer) and their Qt Designer files; `views/sci_spinbox.py` is the spin box with scientific notation they use; `views/reading_panel.py` the plot and LCDs of one reading, shared by the graph window and the graph visualizer; `views/plot_export.py` draws the PNG graph saved next to each CSV file

The `instrument` folder is enough to write your own script or interface; the GUI (in English) needs the whole package.
