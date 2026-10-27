import math
import re
from PyQt6.QtGui import QValidator
from PyQt6.QtWidgets import QAbstractSpinBox, QDoubleSpinBox


# Full or partial float as typed by the user: "2", "2.", "2.5e", "2.5e-", "2.5e-8"
_PARTIAL_FLOAT = re.compile(r"^[+-]?(\d+\.?\d*|\.\d*)?([eE][+-]?\d*)?$")


class SciDoubleSpinBox(QDoubleSpinBox):
    """QDoubleSpinBox that shows very small (or very large) values in scientific notation.

    Values with SCI_LOW <= |v| < SCI_HIGH (and zero) are shown as plain numbers,
    the others as mantissa e exponent (20e-9 s -> "2e-8"). The user can type both forms.
    setDecimals still sets the rounding of the stored value, as in QDoubleSpinBox.
    """
    SCI_LOW = 1e-3
    SCI_HIGH = 1e6
    SIGNIFICANT_DIGITS = 6

    def __init__(self, parent=None):
        super().__init__(parent)
        # Arrows and wheel step by one tenth of the value's decade instead of singleStep
        self.setStepType(QAbstractSpinBox.StepType.AdaptiveDecimalStepType)
        # ((upper limit, resolution), ...) in ascending limits, empty: no grid
        self._resolution: tuple[tuple[float, float], ...] = ()

    def setResolution(self, resolution: tuple[tuple[float, float], ...]) -> None:
        """Instrument resolution grid, e.g. ((1e-3, 2e-7), (3e-3, 1e-4)): 200 ns steps
        up to 1 ms, then 100 us steps up to 3 ms. Above the last limit there is no grid.
        Steps never go below the resolution and typed values are rounded up to it,
        as the instrument does.
        """
        self._resolution = tuple(resolution)

    def stepBy(self, steps: int) -> None:
        if not self._resolution:
            super().stepBy(steps)
            return
        value = self.value()
        resolution = self._resolution_at(value)
        if resolution is None:
            super().stepBy(steps)
            return
        # Same decade step as AdaptiveDecimalStepType, but not below the resolution
        magnitude = abs(value)
        decade_step = 0.0
        if magnitude > 0:
            exponent = math.floor(math.log10(magnitude))
            # Going down from an exact power of ten uses the lower decade (1e-3 -> 9.9e-4)
            if steps < 0 and math.isclose(magnitude, 10.0 ** exponent):
                exponent -= 1
            decade_step = 10.0 ** (exponent - 1)
        step = max(decade_step, resolution)
        new_value = self._snap(value + steps * step, round_up=False)
        self.setValue(min(max(new_value, self.minimum()), self.maximum()))
        self.selectAll()

    def _resolution_at(self, value: float) -> float | None:
        for limit, resolution in self._resolution:
            if abs(value) <= limit * (1 + 1e-9):
                return resolution
        return None

    def _snap(self, value: float, round_up: bool) -> float:
        resolution = self._resolution_at(value)
        if resolution is None:
            return value
        # Tolerance against float noise: 1.0000000001 steps is still 1 step
        ratio = value / resolution
        steps = math.ceil(ratio - 1e-6) if round_up else round(ratio)
        # round: 165 * 2e-7 is 3.2999999999999996e-05 in floats
        return round(steps * resolution, 12)

    def textFromValue(self, value: float) -> str:
        if value == 0 or self.SCI_LOW <= abs(value) < self.SCI_HIGH:
            text = f"{value:.{self.SIGNIFICANT_DIGITS}g}"
            # :g still switches to exponent form for large values, keep it plain here
            if "e" not in text:
                return text
        mantissa, exponent = f"{value:.{self.SIGNIFICANT_DIGITS - 1}e}".split("e")
        mantissa = mantissa.rstrip("0").rstrip(".")
        return f"{mantissa}e{int(exponent)}"

    def valueFromText(self, text: str) -> float:
        try:
            value = float(self._strip_affixes(text))
        except ValueError:
            return self.value()
        return min(self._snap(value, round_up=True), self.maximum())

    def validate(self, text: str, pos: int):
        number = self._strip_affixes(text)
        if not _PARTIAL_FLOAT.match(number):
            return QValidator.State.Invalid, text, pos
        try:
            value = float(number)
        except ValueError:
            return QValidator.State.Intermediate, text, pos
        if self.minimum() <= value <= self.maximum():
            return QValidator.State.Acceptable, text, pos
        return QValidator.State.Intermediate, text, pos

    def fixup(self, text: str) -> str:
        return self.textFromValue(self.value())

    def _strip_affixes(self, text: str) -> str:
        text = text.strip()
        if self.prefix() and text.startswith(self.prefix()):
            text = text[len(self.prefix()):]
        if self.suffix() and text.endswith(self.suffix()):
            text = text[:-len(self.suffix())]
        return text.strip()
