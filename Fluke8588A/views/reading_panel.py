"""Plot and LCDs of one reading, shared by the graph window and the graph visualizer."""
from PyQt6.QtWidgets import QLCDNumber

LCD_DIGITS = 12
# Designer sizes the LCDs for 5 digits, LCD_DIGITS need more room
LCD_MIN_WIDTH = 220
LCD_MIN_HEIGHT = 36
# Fixed so that the two plots line up whatever the tick labels
LEFT_AXIS_WIDTH = 90
POINT_SIZE = 5


def lcd_text(value: float) -> str:
    """Value shown on an LCD of LCD_DIGITS digits."""
    return f"{value:.{LCD_DIGITS - 5}g}"


class ReadingPanel:
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
            axis.setLabel(quantity, units=base_unit or None)
            axis.enableAutoSIPrefix(True)
            self._follow_axis_prefix()
        else:
            # Data stay in the base unit, the axis shows them scaled
            axis.setScale(scale)
            axis.setLabel(f"{quantity} ({unit})", siPrefixEnableRanges=())
            axis.enableAutoSIPrefix(False)
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

    def set_markers(self, markers: bool) -> None:
        """A marker on each point, off for the blocks of samples (too many points)."""
        self._curve.setSymbol("o" if markers else None)

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
            lcd.display("" if value is None else lcd_text(value * self._scale))
