from PyQt6 import uic
from PyQt6.QtWidgets import QFileDialog, QLCDNumber, QWidget
from PyQt6.QtCore import QStandardPaths, pyqtSignal
from Fluke8588A.data import gui_values
from Fluke8588A.views.graph_window import INITIAL_SIZE, SCREEN_FRACTION
from Fluke8588A.views.reading_panel import (
    LCD_DIGITS,
    LCD_MIN_HEIGHT,
    LCD_MIN_WIDTH,
    LEFT_AXIS_WIDTH,
    POINT_SIZE,
)
import math
import numpy as np
import os


digitize_window_loc = os.path.join(
    os.path.dirname(__file__), "..", "ui", "digitize_window.ui"
)


class DigitizeWindow(QWidget):
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    save_requested = pyqtSignal()
    fft_window_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        uic.loadUi(digitize_window_loc, self)
        self.setWindowTitle("DIGITIZE")
        self._resize_to_screen()
        self.fftwin_combobox.addItems(gui_values.DIGI_FFT_WINDOWS)
        self.nsamples_spinbox.setRange(*gui_values.DIGI_NSAMPLES_RANGE)
        self.nsamples_spinbox.setValue(gui_values.DIGI_DEFAULT_NSAMPLES)
        self.samplerate_spinbox.setDecimals(gui_values.DIGI_SAMPLE_RATE_DECIMALS)
        self.samplerate_spinbox.setRange(*gui_values.DIGI_SAMPLE_RATE_RANGE)
        self.samplerate_spinbox.setValue(gui_values.DIGI_DEFAULT_SAMPLE_RATE)
        self.label_3.setText("Peak Freq [Hz]")
        self.label_4.setText("THD [dBc]")
        for lcd in self.sett_groupbox.findChildren(QLCDNumber):
            lcd.setDigitCount(LCD_DIGITS)
            lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
            lcd.setMinimumSize(LCD_MIN_WIDTH, LCD_MIN_HEIGHT)
        self._setup_plots()
        self.start_pushbutton.pressed.connect(self.start_requested)
        self.stop_pushbutton.pressed.connect(self.stop_requested)
        self.save_pushbutton.clicked.connect(self.save_requested)
        self.fftwin_combobox.currentIndexChanged.connect(self.fft_window_changed)
        self.continuous_checkbox.toggled.connect(self._show_continuous)
        self._show_continuous(self.is_continuous())
        self.set_running(False)
        self.set_save_enabled(False)
        self.clear()

    def show_signal(self, quantity: str, base_unit: str) -> None:
        """Show the window for the signal digitized, its unit on the axes."""
        self.label_2.setText(f"Peak Value [{base_unit} rms]")
        self.time_plotwidget.setLabel("left", quantity, units=base_unit)
        self.freq_plotwidget.setLabel("left", f"Magnitude (dB{base_unit})")
        self.show()
        self.raise_()
        self.activateWindow()

    def _setup_plots(self) -> None:
        self.freq_plotwidget.setLabel("bottom", "Frequency", units="Hz")
        self.time_plotwidget.setLabel("bottom", "Time", units="s")
        self._freq_curve = self.freq_plotwidget.plot([], [])
        self._time_curve = self.time_plotwidget.plot([], [], symbol="o", symbolSize=POINT_SIZE)
        for plot in (self.freq_plotwidget, self.time_plotwidget):
            plot.showGrid(x=True, y=True)
            plot.getAxis("left").setWidth(LEFT_AXIS_WIDTH)
            # A block can hold millions of samples, more than the pixels shown
            plot.setDownsampling(auto=True, mode="peak")
            plot.setClipToView(True)

    def _resize_to_screen(self) -> None:
        # The .ui size leaves the plots small: open larger, within the screen
        width, height = INITIAL_SIZE
        screen = self.screen()
        if screen is not None:
            available = screen.availableGeometry()
            width = min(width, int(available.width() * SCREEN_FRACTION))
            height = min(height, int(available.height() * SCREEN_FRACTION))
        self.resize(width, height)

    def is_base_fft(self) -> bool:
        return self.basefft_groupbox.isChecked()

    def samples(self) -> int:
        return self.nsamples_spinbox.value()

    def sample_rate(self) -> float:
        return self.samplerate_spinbox.value()

    def set_sample_rate(self, rate: float) -> None:
        self.samplerate_spinbox.setValue(rate)

    def fft_window(self) -> str:
        return self.fftwin_combobox.currentText()

    def is_continuous(self) -> bool:
        return self.continuous_checkbox.isChecked()

    def is_averaged(self) -> bool:
        # Unchecked by _show_continuous out of continuous mode
        return self.averaged_checkbox.isChecked()

    def _show_continuous(self, continuous: bool) -> None:
        # Burst count and averaging have a meaning only with more blocks
        self.label_7.setVisible(continuous)
        self.nburst_lcdnumber.setVisible(continuous)
        self.averaged_checkbox.setEnabled(continuous and self.start_pushbutton.isEnabled())
        if not continuous:
            self.averaged_checkbox.setChecked(False)

    def set_burst_count(self, count: int) -> None:
        self.nburst_lcdnumber.display(count)

    def set_running(self, running: bool) -> None:
        self.start_pushbutton.setEnabled(not running)
        self.stop_pushbutton.setEnabled(running)
        # The trigger is set at Start, a change in the meanwhile would not apply
        self.basefft_groupbox.setEnabled(not running)
        self.continuous_checkbox.setEnabled(not running)
        self.averaged_checkbox.setEnabled(not running and self.is_continuous())

    def set_save_enabled(self, enabled: bool) -> None:
        self.save_pushbutton.setEnabled(enabled)

    def set_time_curve(self, values, rate: float | None) -> None:
        """Block acquired, nan for the samples left out; on the sample number when the rate is unknown."""
        x = np.arange(len(values))
        if rate is None:
            self.time_plotwidget.setLabel("bottom", "Sample", units=None)
        else:
            x = x / rate
            self.time_plotwidget.setLabel("bottom", "Time", units="s")
        self._time_curve.setData(x, values, connect="finite")
        self.time_plotwidget.enableAutoRange()

    def set_frequency_curve(self, freqs, magnitude_db) -> None:
        # A bin at exactly zero is -inf dB, the curve cannot draw it
        finite = np.where(np.isfinite(magnitude_db), magnitude_db, np.nan)
        self._freq_curve.setData(freqs, finite, connect="finite")
        self.freq_plotwidget.enableAutoRange()

    def set_results(self, peak: float, peak_frequency: float, thd_dbc: float) -> None:
        for lcd, value in (
            (self.peakval_lcdnumber, peak),
            (self.peakfreq_lcdnumber, peak_frequency),
            (self.thd_lcdnumber, thd_dbc),
        ):
            lcd.display(f"{value:.{LCD_DIGITS - 5}g}" if math.isfinite(value) else "")

    def clear_fft(self) -> None:
        self._freq_curve.setData([], [])
        for lcd in (self.peakval_lcdnumber, self.peakfreq_lcdnumber, self.thd_lcdnumber):
            lcd.display("")

    def clear(self) -> None:
        self._time_curve.setData([], [])
        self.clear_fft()
        self.set_burst_count(0)

    def ask_save_path(self, name: str, directory: str | None = None) -> str | None:
        """Save dialog with a proposed file name, None when cancelled; Documents when no directory."""
        if directory is None:
            directory = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        path, _ = QFileDialog.getSaveFileName(
            self, "Save measurement", os.path.join(directory, name), "CSV files (*.csv);;All files (*)"
        )
        return path or None
