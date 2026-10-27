from PyQt6 import uic
from PyQt6.QtWidgets import QLCDNumber, QWidget
from PyQt6.QtCore import pyqtSignal
import os


graph_window_loc = os.path.join(
    os.path.dirname(__file__), "..", "ui", "graph_window.ui"
)

LCD_DIGITS = 12
# Designer sizes the LCDs for 5 digits, LCD_DIGITS need more room
LCD_MIN_WIDTH = 220
LCD_MIN_HEIGHT = 36
# Fixed so that the two plots line up whatever the tick labels
LEFT_AXIS_WIDTH = 90
POINT_SIZE = 5
INITIAL_SIZE = (1150, 830)
SCREEN_FRACTION = 0.9


class _ReadingPanel:
    """
    Plot and statistics LCDs of one reading (primary or secondary): data and
    statistics arrive in the base unit (V, A, Ω, Hz...), the LCDs show them
    scaled to the unit.
    """

    def __init__(self, title: str, plot_widget, meas_groupbox, nrdgs_lcd, value_lcds):
        self._title = title
        self._plot_widget = plot_widget
        self._meas_groupbox = meas_groupbox
        self._nrdgs_lcd = nrdgs_lcd
        # value, mean, stdev, stdev of the mean
        self._value_lcds = value_lcds
        self._scale = 1.0
        # Base unit when the axis picks the SI prefix (AUTO), None otherwise
        self._auto_base_unit = None
        self._statistics = (0, None, None, None, None)
        # A marker on each reading, the line stays
        self._curve = plot_widget.plot([], [], symbol="o", symbolSize=POINT_SIZE)
        plot_widget.setLabel("bottom", "Time", units="s")
        plot_widget.showGrid(x=True, y=True)
        plot_widget.getAxis("left").setWidth(LEFT_AXIS_WIDTH)
        for lcd in meas_groupbox.findChildren(QLCDNumber):
            lcd.setDigitCount(LCD_DIGITS)
            lcd.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
            lcd.setMinimumSize(LCD_MIN_WIDTH, LCD_MIN_HEIGHT)
        # Connected after the axis, which updates its SI prefix first
        plot_widget.getViewBox().sigYRangeChanged.connect(self._follow_axis_prefix)

    @property
    def meas_groupbox(self):
        return self._meas_groupbox

    def set_unit(self, quantity: str, base_unit: str, unit: str | None = None, scale: float = 1.0) -> None:
        axis = self._plot_widget.getAxis("left")
        self._auto_base_unit = base_unit if unit is None else None
        if unit is None:
            axis.setScale(1.0)
            axis.enableAutoSIPrefix(True)
            self._plot_widget.setLabel("left", quantity, units=base_unit or None)
            self._follow_axis_prefix()
        else:
            # Data stay in the base unit, the axis shows them scaled
            axis.setScale(scale)
            axis.enableAutoSIPrefix(False)
            self._plot_widget.setLabel("left", f"{quantity} ({unit})")
            self._show_unit(unit, scale)

    def _follow_axis_prefix(self) -> None:
        # AUTO: the axis picks the SI prefix from the shown range, the LCDs
        # take the same one so that both are in the same unit
        if self._auto_base_unit is None:
            return
        axis = self._plot_widget.getAxis("left")
        self._show_unit(f"{axis.labelUnitPrefix}{self._auto_base_unit}", axis.autoSIPrefixScale)

    def _show_unit(self, unit: str, scale: float) -> None:
        self._scale = scale
        suffix = f" [{unit}]" if unit else ""
        self._meas_groupbox.setTitle(f"{self._title}{suffix}")
        self._show_statistics()

    def set_curve(self, times: list[float], values: list[float]) -> None:
        self._curve.setData(times, values)

    def set_statistics(self, count, value, mean, stdev, stdev_mean) -> None:
        self._statistics = (count, value, mean, stdev, stdev_mean)
        self._show_statistics()

    def clear(self) -> None:
        self.set_curve([], [])
        self.set_statistics(0, None, None, None, None)

    def _show_statistics(self) -> None:
        count, *values = self._statistics
        self._nrdgs_lcd.display(count)
        for lcd, value in zip(self._value_lcds, values):
            lcd.display("" if value is None else self._lcd_text(value * self._scale))

    @staticmethod
    def _lcd_text(value: float) -> str:
        return f"{value:.{LCD_DIGITS - 5}g}"


class GraphWindow(QWidget):
    start_requested = pyqtSignal()
    stop_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        uic.loadUi(graph_window_loc, self)
        self.setWindowTitle("Graph")
        self._resize_to_screen()
        # Display only: data and statistics come from AcquisitionController
        self._primary = _ReadingPanel(
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
        self._secondary = _ReadingPanel(
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
        self.set_running(False)
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

    def clear(self) -> None:
        self._primary.clear()
        self._secondary.clear()

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
