"""CSV file of an acquisition, in the temp folder of the project (last files only)."""
from dataclasses import fields
from datetime import datetime
from pathlib import Path
from Fluke8588A.data import gui_values
import os
import shutil
import time

TEMP_DIR = Path(__file__).resolve().parents[2] / "temp"
TEMP_PREFIX = "temp_"
MAX_TEMP_FILES = 3
# Interval of the writes to disk (fsync): at most this much of the readings
# is lost in a blackout, without a disk write at every answer
SYNC_INTERVAL = 1.0  # s

# Settings fields already shown as range and digits in the Measurement line
_MAIN_FIELDS = ("range_mode", "range_val", "resolution")

# Characters of the range labels that do not belong in a file name
_FILENAME_REPLACEMENTS = {" ": "", "Ω": "Ohm", "μ": "u", "µ": "u"}


class MeasurementFile:
    """
    CSV file of one acquisition:

        # Fluke8588A
        # Measurement: <function> <range> <digits> <other settings>
        # ...
        timestamp,time,value[,secvalue]

    The rows are written (and flushed) as the readings arrive and forced to
    disk every SYNC_INTERVAL, so an interrupted acquisition (crash, blackout)
    keeps its data up to the last second; the statistics in the header are
    known only at the end and written by close(). Overloads have an empty
    value, as the secondary readings not available.

    Only the last MAX_TEMP_FILES files are kept: opening a new one deletes
    the oldest ones.
    """

    def __init__(self, function: str, settings, units: tuple[str, ...], secondary_reading: str | None = None,
                 directory: Path = TEMP_DIR):
        self._secondary = secondary_reading is not None
        self._start = datetime.now()
        self._measurement = _measurement_line(function, settings)
        self._units = units
        directory.mkdir(parents=True, exist_ok=True)
        _remove_oldest(directory, MAX_TEMP_FILES - 1)
        self.path = _new_path(directory, self._start, _range_label(settings))
        self._file = open(self.path, "w", encoding="utf-8", newline="")
        self._file.write(self._header(None, None))
        self._sync()

    def add_rows(self, timestamp: datetime, elapsed: float, values: list[str],
                 secondary_values: list[str] | None = None) -> None:
        """Rows of the readings of one answer, all with the same time; values as read ('' for overloads)."""
        for index, value in enumerate(values):
            row = [timestamp.isoformat(timespec="milliseconds"), f"{elapsed:.6f}", value]
            if self._secondary:
                row.append(secondary_values[index] if secondary_values and index < len(secondary_values) else "")
            self._file.write(",".join(row) + "\n")
        self._file.flush()
        if time.monotonic() - self._last_sync >= SYNC_INTERVAL:
            self._sync()

    def close(self, statistics, secondary_statistics=None) -> None:
        """Write the final statistics in the header and close the file."""
        if self._file.closed:
            return
        self._sync()
        self._file.close()
        with open(self.path, encoding="utf-8", newline="") as file:
            lines = file.readlines()
        # The data rows follow the column names, the first line not a comment nor empty
        columns_index = next(i for i, line in enumerate(lines) if line.strip() and not line.startswith("#"))
        rows = lines[columns_index + 1:]
        temp_path = self.path.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8", newline="") as file:
            file.write(self._header(statistics, secondary_statistics))
            file.writelines(rows)
            # On disk before the replace: after a blackout the file is the old
            # one or the new one, never an empty one
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, self.path)

    def _sync(self) -> None:
        """Write the rows to disk, not only to the Windows cache."""
        self._file.flush()
        os.fsync(self._file.fileno())
        self._last_sync = time.monotonic()

    def _header(self, statistics, secondary_statistics) -> str:
        lines = [
            "Fluke8588A",
            f"Measurement: {self._measurement}",
            f"Unit: {', '.join(self._units)}",
            f"Date time: {self._start.isoformat(sep=' ', timespec='seconds')}",
        ]
        lines += _statistics_lines("", statistics)
        if self._secondary:
            lines += _statistics_lines("Secondary ", secondary_statistics)
        columns = "timestamp,time,value,secvalue" if self._secondary else "timestamp,time,value"
        return "".join(f"# {line}\n" for line in lines) + "\n" + columns + "\n"


def read_primary(path: Path) -> tuple[list[float], list[float]]:
    """Times and values of the primary readings of a file, overloads (empty values) left out."""
    times = []
    values = []
    with open(path, encoding="utf-8", newline="") as file:
        lines = iter(file)
        # The data rows follow the column names, the first line not a comment nor empty
        for line in lines:
            if line.strip() and not line.startswith("#"):
                break
        for line in lines:
            row = line.rstrip("\r\n").split(",")
            if len(row) < 3 or not row[2]:
                continue
            times.append(float(row[1]))
            values.append(float(row[2]))
    return times, values


def saved_name(path: Path) -> str:
    """Default name of a copy of a temp file: the same without the temp prefix."""
    return path.name.removeprefix(TEMP_PREFIX)


def save_copy(path: Path, destination: Path) -> Path:
    """Copy a closed temp file to destination, .csv added when it has no suffix."""
    if not destination.suffix:
        destination = destination.with_suffix(".csv")
    shutil.copyfile(path, destination)
    return destination


def _statistics_lines(prefix: str, statistics) -> list[str]:
    def text(value):
        return "" if value is None else repr(value)

    if statistics is None:
        return [f"{prefix}Nrdgs: 0", f"{prefix}Avg: ", f"{prefix}Stdev: ", f"{prefix}Stdevavg: "]
    return [
        f"{prefix}Nrdgs: {statistics.count}",
        f"{prefix}Avg: {text(statistics.mean)}",
        f"{prefix}Stdev: {text(statistics.stdev)}",
        f"{prefix}Stdevavg: {text(statistics.stdev_mean)}",
    ]


def _range_label(settings) -> str:
    """'AUTO' in autorange, otherwise the range label ('100 mV')."""
    if getattr(settings, "range_mode", None) == gui_values.RANGE_MODE_AUTO:
        return gui_values.RANGE_MODE_AUTO
    return settings.range_val


def _measurement_line(function: str, settings) -> str:
    """'DCV 10 V 8 digits zin=10 MΩ ...': function, range, digits, then the other settings."""
    parts = [function, _range_label(settings)]
    if hasattr(settings, "resolution"):
        parts.append(f"{settings.resolution} digits")
    for field in fields(settings):
        if field.name not in _MAIN_FIELDS:
            parts.append(f"{field.name}={getattr(settings, field.name)}")
    return " ".join(parts)


def _new_path(directory: Path, start: datetime, range_label: str) -> Path:
    """temp_<datetime>_<range>.csv, with a counter if a file started in the same second exists."""
    for old, new in _FILENAME_REPLACEMENTS.items():
        range_label = range_label.replace(old, new)
    stem = f"{TEMP_PREFIX}{start:%Y%m%d_%H%M%S}_{range_label}"
    path = directory / f"{stem}.csv"
    counter = 1
    while path.exists():
        path = directory / f"{stem}_{counter}.csv"
        counter += 1
    return path


def _remove_oldest(directory: Path, keep: int) -> None:
    """Delete the oldest temp files, keeping the newest `keep`."""
    files = sorted(directory.glob(f"{TEMP_PREFIX}*.csv"), key=lambda path: path.stat().st_mtime)
    for path in files[: max(len(files) - keep, 0)]:
        path.unlink()
