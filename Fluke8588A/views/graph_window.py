from PyQt6 import uic
from PyQt6.QtWidgets import QFileDialog, QWidget
from PyQt6.QtCore import QStandardPaths, pyqtSignal
from Fluke8588A.views.reading_panel import POINT_SIZE, ReadingPanel
import os


graph_window_loc = os.path.join(
    os.path.dirname(__file__), "..", "ui", "graph_window.ui"
)

INITIAL_SIZE = (1150, 830)
SCREEN_FRACTION = 0.9


class GraphWindow(QWidget):
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()
    save_requested = pyqtSignal()
    allan_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        uic.loadUi(graph_window_loc, self)
        self.setWindowTitle("Graph")
        self._resize_to_screen()
        # Display only: data and statistics come from AcquisitionController
        self._primary = ReadingPanel(
            "Primary Measurement",
            self.prim_plotwidget,
            self.prim_meas_groupbox,
            self.prim_nrdgs_lcdnumber,
            (
                self.prim_value_lcdnumber,
                self.prim_avg_lcdnumber,
                self.prim_stdev_lcdnumber,
                self.prim_stdevavg_lcdnumber,
            ),
        )
        self._secondary = ReadingPanel(
            "Secondary Measurement",
            self.sec_plotwidget,
            self.sec_meas_groupbox,
            self.sec_nrdgs_lcdnumber,
            (
                self.sec_value_lcdnumber,
                self.sec_avg_lcdnumber,
                self.sec_stdev_lcdnumber,
                self.sec_stdevavg_lcdnumber,
            ),
        )
        self.start_pushbutton.pressed.connect(self.start_requested)
        self.stop_pushbutton.pressed.connect(self.stop_requested)
        self.save_pushbutton.clicked.connect(self.save_requested)
        self.allan_generate_pushbutton.clicked.connect(self.allan_requested)
        self.secread_checkbox.toggled.connect(self.sec_groupbox.setVisible)
        self._setup_allan_plot()
        self.set_running(False)
        self.set_save_enabled(False)
        self.set_allan_enabled(False)
        self.set_primary_unit("Reading", "")
        self.set_secondary_unit("Reading", "")
        self.set_secondary_reading(None)

    def show_function(self, function: str, secondary_reading: str | None = None):
        """Show the window for a function, secondary_reading is None when OFF."""
        self.setWindowTitle(f"{function} Graph")
        self.set_secondary_reading(secondary_reading)
        # Units of the previous function no longer apply
        self.set_primary_unit("Reading", "")
        self.set_secondary_unit("Reading", "")
        self.show()
        self.raise_()
        self.activateWindow()

    def set_secondary_reading(self, secondary_reading: str | None) -> None:
        # Hidden, the primary reading takes the whole window
        visible = secondary_reading is not None
        # Checked by default: unchecking only hides the secondary groupbox
        self.secread_checkbox.setVisible(visible)
        self.secread_checkbox.setChecked(True)
        self.sec_groupbox.setVisible(visible)
        if visible:
            self.sec_groupbox.setTitle(f"Secondary Reading: {secondary_reading}")

    def set_primary_unit(self, quantity: str, base_unit: str, unit: str | None = None, scale: float = 1.0) -> None:
        """
        Unit of the primary axis and values: readings arrive in base_unit and are
        shown in unit (value * scale). With unit None (AUTO range) the axis picks
        its own SI prefix and the values are shown in base_unit.
        """
        self._primary.set_unit(quantity, base_unit, unit, scale)
        self._align_panels()

    def set_secondary_unit(self, quantity: str, base_unit: str, unit: str | None = None, scale: float = 1.0) -> None:
        """Unit of the secondary axis and values, as set_primary_unit."""
        self._secondary.set_unit(quantity, base_unit, unit, scale)
        self._align_panels()

    def _resize_to_screen(self) -> None:
        # The .ui size leaves the plots small: open larger, within the screen
        width, height = INITIAL_SIZE
        screen = self.screen()
        if screen is not None:
            available = screen.availableGeometry()
            width = min(width, int(available.width() * SCREEN_FRACTION))
            height = min(height, int(available.height() * SCREEN_FRACTION))
        self.resize(width, height)

    def _align_panels(self) -> None:
        # The groupbox width follows its title (unit suffix): same width for
        # both, so that the two plots start at the same x
        groupboxes = (self._primary.meas_groupbox, self._secondary.meas_groupbox)
        for groupbox in groupboxes:
            groupbox.setMinimumWidth(0)
        width = max(groupbox.sizeHint().width() for groupbox in groupboxes)
        for groupbox in groupboxes:
            groupbox.setFixedWidth(width)

    def set_running(self, running: bool) -> None:
        self.start_pushbutton.setEnabled(not running)
        self.stop_pushbutton.setEnabled(running)

    def set_save_enabled(self, enabled: bool) -> None:
        self.save_pushbutton.setEnabled(enabled)

    def set_allan_enabled(self, enabled: bool) -> None:
        self.allan_generate_pushbutton.setEnabled(enabled)

    def _setup_allan_plot(self) -> None:
        plot = self.allan_plotwidget
        self._allan_curve = plot.plot([], [], symbol="o", symbolSize=POINT_SIZE)
        plot.setLogMode(x=True, y=True)
        plot.showGrid(x=True, y=True)
        plot.setLabel("bottom", "Tau (s)")
        self._set_allan_unit("")

    def _set_allan_unit(self, base_unit: str) -> None:
        # Log axes: the SI prefix of the axis does not apply, the unit goes in the label
        suffix = f" ({base_unit})" if base_unit else ""
        self.allan_plotwidget.setLabel("left", f"Allan deviation{suffix}")

    def set_allan_curve(self, taus, adevs, base_unit: str) -> None:
        """Allan deviation of the primary reading, tau in s and adev in base_unit, shown in its tab."""
        self._set_allan_unit(base_unit)
        self._allan_curve.setData(taus, adevs)
        self.allan_plotwidget.enableAutoRange()
        self.tabWidget.setCurrentWidget(self.allan_tab)

    def clear_allan(self) -> None:
        self._allan_curve.setData([], [])

    def ask_save_path(self, name: str, directory: str | None = None) -> str | None:
        """Save dialog with a proposed file name, None when cancelled; Documents when no directory."""
        if directory is None:
            directory = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        path, _ = QFileDialog.getSaveFileName(
            self, "Save measurement", os.path.join(directory, name), "CSV files (*.csv);;All files (*)"
        )
        return path or None

    def clear(self) -> None:
        self._primary.clear()
        self._secondary.clear()
        self.clear_allan()

    def set_primary_curve(self, times: list[float], values: list[float]) -> None:
        """Time in s from the first reading, values in the base unit."""
        self._primary.set_curve(times, values)

    def set_secondary_curve(self, times: list[float], values: list[float]) -> None:
        """Time in s from the first reading, values in the base unit."""
        self._secondary.set_curve(times, values)

    def set_primary_statistics(
        self,
        count: int,
        value: float | None,
        mean: float | None,
        stdev: float | None,
        stdev_mean: float | None,
    ) -> None:
        """Statistics in the base unit, None when not available (no reading, stdev with one)."""
        self._primary.set_statistics(count, value, mean, stdev, stdev_mean)

    def set_secondary_statistics(
        self,
        count: int,
        value: float | None,
        mean: float | None,
        stdev: float | None,
        stdev_mean: float | None,
    ) -> None:
        """Statistics in the base unit, as set_primary_statistics."""
        self._secondary.set_statistics(count, value, mean, stdev, stdev_mean)
