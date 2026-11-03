from PyQt6 import uic
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget
from PyQt6.QtCore import QStandardPaths, pyqtSignal
from Fluke8588A.views.graph_window import INITIAL_SIZE, SCREEN_FRACTION
from Fluke8588A.views.reading_panel import ReadingPanel, lcd_text
import os


graph_visualizer_loc = os.path.join(
    os.path.dirname(__file__), "..", "ui", "graph_visualizer.ui"
)

PANELS = ("prim", "sec")
# Labels of the LCDs of a graph: readings, digitize block ({unit}: its base unit)
_READING_LABELS = ("N rdgs", "Value", "Avg", "St Dev", "St Dev Avg")
_DIGITIZE_LABELS = ("Samples", "Sample rate [Hz]", "Peak [{unit} rms]", "Peak freq [Hz]", "THD [dBc]")


class GraphVisualizerWindow(QWidget):
    """Viewer of the measurement files saved, independent of the instrument."""

    # Panel ('prim' or 'sec') whose Import was pressed
    import_requested = pyqtSignal(str)
    ignore_secondary_changed = pyqtSignal(bool)
    # Panel and burst chosen in it, 1 the first of the file
    burst_changed = pyqtSignal(str, int)

    def __init__(self):
        super().__init__()
        uic.loadUi(graph_visualizer_loc, self)
        self.setWindowTitle("GRAPH VISUALIZER")
        self._resize_to_screen()
        self._groupboxes = {"prim": self.prim_groupbox, "sec": self.sec_groupbox}
        self._group_titles = {panel: groupbox.title() for panel, groupbox in self._groupboxes.items()}
        self._panels = {
            panel: ReadingPanel(
                "Statistical Values",
                getattr(self, f"{panel}_plotwidget"),
                getattr(self, f"{panel}_meas_groupbox"),
                getattr(self, f"{panel}_nrdgs_lcdnumber"),
                tuple(
                    getattr(self, f"{panel}_{name}_lcdnumber")
                    for name in ("value", "avg", "stdev", "stdevavg")
                ),
            )
            for panel in PANELS
        }
        self._burst_widgets = {
            "prim": (self.label, self.prim_burst_spinbox),
            "sec": (self.label_2, self.sec_burst_spinbox),
        }
        self._lcd_labels = {
            "prim": (self.label_4, self.label_9, self.label_5, self.label_6, self.label_8),
            "sec": (self.label_14, self.label_15, self.label_16, self.label_17, self.label_18),
        }
        self._lcds = {
            panel: tuple(
                getattr(self, f"{panel}_{name}_lcdnumber")
                for name in ("nrdgs", "value", "avg", "stdev", "stdevavg")
            )
            for panel in PANELS
        }
        for panel in PANELS:
            plot = getattr(self, f"{panel}_plotwidget")
            # A digitize block can hold millions of samples, more than the pixels shown
            plot.setDownsampling(auto=True, mode="peak")
            plot.setClipToView(True)
        self.prim_burst_spinbox.valueChanged.connect(lambda number: self.burst_changed.emit("prim", number))
        self.sec_burst_spinbox.valueChanged.connect(lambda number: self.burst_changed.emit("sec", number))
        self.prim_import_pushbutton.clicked.connect(lambda: self.import_requested.emit("prim"))
        self.sec_import_pushbutton.clicked.connect(lambda: self.import_requested.emit("sec"))
        self.prim_ignoresec_checkbox.toggled.connect(self.ignore_secondary_changed)
        self.twograph_checkbox.toggled.connect(self.sec_groupbox.setVisible)
        self.sec_groupbox.setVisible(self.twograph_checkbox.isChecked())
        self._last_directory = None
        for panel in PANELS:
            self.clear(panel)

    def is_ignore_secondary(self) -> bool:
        """Secondary readings of the file imported in the first graph not shown."""
        return self.prim_ignoresec_checkbox.isChecked()

    def show_second_graph(self) -> None:
        self.twograph_checkbox.setChecked(True)

    def set_burst_count(self, panel: str, count: int) -> None:
        """
        Bursts of the digitize file loaded in panel ('prim' or 'sec'), 0 out of
        continuous mode: the spinbox only then, back on the first burst.
        """
        label, spinbox = self._burst_widgets[panel]
        # The controller shows the first burst itself
        spinbox.blockSignals(True)
        spinbox.setRange(1, max(count, 1))
        spinbox.setValue(1)
        spinbox.blockSignals(False)
        label.setVisible(count > 0)
        spinbox.setVisible(count > 0)

    def set_digitize_values(self, panel: str, base_unit: str, samples: int | None, rate: float | None,
                            peak: float | None, peak_frequency: float | None, thd_dbc: float | None) -> None:
        """
        LCDs of a graph for a digitize block, in place of the statistics:
        values in base unit, Hz and dBc, None when not available. Call after
        set_unit(), which shows the statistics again.
        """
        for label, text in zip(self._lcd_labels[panel], _DIGITIZE_LABELS):
            label.setText(text.format(unit=base_unit))
        getattr(self, f"{panel}_meas_groupbox").setTitle("Block Values")
        lcds = self._lcds[panel]
        lcds[0].display("" if samples is None else samples)
        for lcd, value in zip(lcds[1:], (rate, peak, peak_frequency, thd_dbc)):
            lcd.display("" if value is None else lcd_text(value))

    def set_values_visible(self, panel: str, visible: bool) -> None:
        """LCDs of the graph, hidden for a spectrum."""
        getattr(self, f"{panel}_meas_groupbox").setVisible(visible)

    def set_x_label(self, panel: str, label: str, units: str | None) -> None:
        getattr(self, f"{panel}_plotwidget").setLabel("bottom", label, units=units)

    def set_markers(self, panel: str, markers: bool) -> None:
        """A marker on each point: on for the readings, off for samples and spectra."""
        self._panels[panel].set_markers(markers)

    def set_file_title(self, panel: str, title: str) -> None:
        """Graph title followed by the file shown ('Graph: DCV 20261102_122700_1V.csv')."""
        self._groupboxes[panel].setTitle(f"{self._group_titles[panel]}: {title}")

    def set_unit(self, panel: str, quantity: str, base_unit: str, unit: str | None = None,
                 scale: float = 1.0) -> None:
        """Unit of axis and LCDs, as GraphWindow.set_primary_unit."""
        self._panels[panel].set_unit(quantity, base_unit, unit, scale)

    def set_curve(self, panel: str, times: list[float], values: list[float]) -> None:
        self._panels[panel].set_curve(times, values)
        getattr(self, f"{panel}_plotwidget").enableAutoRange()

    def set_statistics(self, panel: str, count: int, value: float | None, mean: float | None,
                       stdev: float | None, stdev_mean: float | None) -> None:
        """Statistics in the base unit, None when not available."""
        self._panels[panel].set_statistics(count, value, mean, stdev, stdev_mean)

    def clear(self, panel: str) -> None:
        """Empty graph, ready for the readings of a measurement file."""
        self._panels[panel].clear()
        self._groupboxes[panel].setTitle(self._group_titles[panel])
        self.set_burst_count(panel, 0)
        self.set_markers(panel, True)
        self.set_values_visible(panel, True)
        self.set_x_label(panel, "Time", "s")
        for label, text in zip(self._lcd_labels[panel], _READING_LABELS):
            label.setText(text)
        self.set_unit(panel, "Reading", "")

    def ask_open_path(self) -> str | None:
        """Open dialog of a CSV file, None when cancelled; the last folder used, Documents at first."""
        directory = self._last_directory or QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.DocumentsLocation
        )
        path, _ = QFileDialog.getOpenFileName(
            self, "Import measurement", directory, "CSV files (*.csv);;All files (*)"
        )
        if not path:
            return None
        self._last_directory = os.path.dirname(path)
        return path

    def show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Import measurement", message)

    def show_information(self, message: str) -> None:
        QMessageBox.information(self, "Import measurement", message)

    def show_window(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def _resize_to_screen(self) -> None:
        width, height = INITIAL_SIZE
        screen = self.screen()
        if screen is not None:
            available = screen.availableGeometry()
            width = min(width, int(available.width() * SCREEN_FRACTION))
            height = min(height, int(available.height() * SCREEN_FRACTION))
        self.resize(width, height)
