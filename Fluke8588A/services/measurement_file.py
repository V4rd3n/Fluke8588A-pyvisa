"""
CSV files of the acquisitions, in the temp folder of the project (last ones
only), named temp_<date>_<time>_<range>.csv, the range with its unit
('100mV', 'AUTO_V' in autorange), and temp_<date>_<time>_<time|freq>_<range>.csv
for the two files of a digitize acquisition (samples and spectrum). The PNG
of the graph of a file has the same name, .png. The files are read back by
services/measurement_reader.
"""
from dataclasses import fields
from datetime import datetime
from pathlib import Path
from Fluke8588A.data import gui_values
import numpy as np
import os
import shutil
import time

TEMP_DIR = Path(__file__).resolve().parents[2] / "temp"
# Acquisitions kept in TEMP_DIR: files with the same date and time (the two
# files of a digitize block and their graphs) belong to the same acquisition
MAX_TEMP_FILES = 10
TEMP_PREFIX = "temp_"
# Glob of the files named by new_temp_path(): temp_<YYYYmmdd>_<HHMMSS>_...
_TEMP_GLOB = TEMP_PREFIX + "[0-9]" * 8 + "_" + "[0-9]" * 6 + "_*"
_STAMP_END = len(TEMP_PREFIX) + len("YYYYmmdd_HHMMSS")
# Interval of the writes to disk (fsync): at most this much of the readings
# is lost in a blackout, without a disk write at every answer
SYNC_INTERVAL = 1.0  # s

# Settings fields already shown as range and digits in the Measurement line
_MAIN_FIELDS = ("range_mode", "range_val", "resolution")

# Characters of the range labels that do not belong in a file name
_FILENAME_REPLACEMENTS = {" ": "", "Ω": "Ohm", "μ": "u", "µ": "u"}
# Labels of the two files of a digitize acquisition
DIGITIZE_TIME_LABEL = "time"
DIGITIZE_FREQUENCY_LABEL = "freq"
DIGITIZE_AVERAGE_LABEL = "avg"

# First line of the header of every file, read back by services/measurement_reader
SIGNATURE = "Fluke8588A"
# Statistics keys of the header, in their order, without the "Secondary " prefix
STATISTICS_KEYS = ("Nrdgs", "Avg", "Stdev", "Stdevavg")


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

    Only the last MAX_TEMP_FILES acquisitions are kept: opening a new file
    deletes the oldest ones, with their graphs.
    """

    def __init__(self, function: str, settings, units: tuple[str, ...], secondary_reading: str | None = None,
                 directory: Path = TEMP_DIR):
        self._secondary = secondary_reading is not None
        self._start = datetime.now()
        self._measurement = _measurement_line(function, settings)
        self._units = units
        clean_temp(directory)
        self.path = new_temp_path(self._start, _file_range_label(settings, units[0]), directory)
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
            SIGNATURE,
            f"Measurement: {self._measurement}",
            f"Unit: {', '.join(self._units)}",
            f"Date time: {self._start.isoformat(sep=' ', timespec='seconds')}",
        ]
        lines += statistics_lines("", statistics)
        if self._secondary:
            lines += statistics_lines("Secondary ", secondary_statistics)
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


def png_path(path: Path) -> Path:
    """PNG of the graph of a file: same name, .png."""
    return path.with_suffix(".png")


def saved_name(path: Path) -> str:
    """Default name of a copy of a temp file: the same without the temp prefix."""
    return path.name.removeprefix(TEMP_PREFIX)


def save_copy(path: Path, destination: Path) -> tuple[Path, Path | None]:
    """
    Copy a closed temp file to destination, .csv added when it has no suffix,
    and the PNG of its graph next to it with the same name. Returns the two
    paths, the PNG one None when the temp file has no graph.
    """
    if not destination.suffix:
        destination = destination.with_suffix(".csv")
    shutil.copyfile(path, destination)
    if not png_path(path).exists():
        return destination, None
    shutil.copyfile(png_path(path), png_path(destination))
    return destination, png_path(destination)


def clean_temp(directory: Path = TEMP_DIR) -> None:
    """Folder ready for a new acquisition: created if missing, only the newest MAX_TEMP_FILES - 1 kept."""
    directory.mkdir(parents=True, exist_ok=True)
    _remove_oldest(directory, MAX_TEMP_FILES - 1)


def new_temp_path(start: datetime, label: str, directory: Path = TEMP_DIR) -> Path:
    """temp_<datetime>_<label>.csv, with a counter if a file with the same name exists."""
    for old, new in _FILENAME_REPLACEMENTS.items():
        label = label.replace(old, new)
    stem = f"{TEMP_PREFIX}{start:%Y%m%d_%H%M%S}_{label}"
    path = directory / f"{stem}.csv"
    counter = 1
    while path.exists():
        path = directory / f"{stem}_{counter}.csv"
        counter += 1
    return path


def digitize_time_label(settings) -> str:
    """Label of the samples file of a digitize acquisition: 'time_<range>' ('time_1 V')."""
    return f"{DIGITIZE_TIME_LABEL}_{_range_label(settings)}"


def digitize_frequency_name(time_path: Path) -> Path:
    """
    Spectrum file of a digitize samples file: the last '_time' becomes '_freq'
    (temp_<stamp>_time_1V.csv -> temp_<stamp>_freq_1V.csv), else <name>_freq.csv.
    """
    head, separator, tail = time_path.stem.rpartition(f"_{DIGITIZE_TIME_LABEL}")
    stem = f"{head}_{DIGITIZE_FREQUENCY_LABEL}{tail}" if separator else f"{time_path.stem}_{DIGITIZE_FREQUENCY_LABEL}"
    return time_path.with_name(f"{stem}{time_path.suffix}")


def digitize_average_name(path: Path) -> Path:
    """
    File of the average of the bursts: <name>_avg (temp_<stamp>_time_1V.csv ->
    temp_<stamp>_time_1V_avg.csv), its spectrum is digitize_frequency_name() of it.
    """
    return path.with_name(f"{path.stem}_{DIGITIZE_AVERAGE_LABEL}{path.suffix}")


def write_digitize_header(path: Path, start: datetime, settings, unit: str, count: int, rate: float | None,
                          continuous: bool, averaged: int | None = None) -> Path:
    """
    New CSV file of the samples of a digitize acquisition, .csv added when it
    has no suffix: header and column names, the blocks follow with
    append_digitize_block(). count is the number of samples of each block,
    averaged the number of bursts for a file of their average.
    """
    if not path.suffix:
        path = path.with_suffix(".csv")
    x_name = "sample" if rate is None else "time"
    header = _digitize_header(start, settings, unit, count, rate, continuous, _average_lines(averaged))
    with open(path, "w", encoding="utf-8", newline="") as file:
        file.write(f"{header}{x_name},value\n")
    return path


def append_digitize_block(path: Path, values, rate: float | None, burst: int | None = None) -> None:
    """
    Samples of a block at the end of the file: time from the start of the
    block (sample number when the rate is unknown) and value, overloads as
    nan. In continuous mode a '# burst N' line comes before each block.
    """
    x = np.arange(len(values)) if rate is None else np.arange(len(values)) / rate
    with open(path, "a", encoding="utf-8", newline="") as file:
        if burst is not None:
            file.write(f"# burst {burst}\n")
        np.savetxt(file, np.column_stack((x, values)), fmt=("%.12g", "%.9E"), delimiter=",")


def write_digitize_time(path: Path, start: datetime, settings, unit: str, values, rate: float | None,
                        continuous: bool = False, burst: int | None = None, averaged: int | None = None) -> Path:
    """
    CSV file of the samples of one block, burst its number in continuous mode;
    averaged the number of bursts when the block is their average.
    """
    path = write_digitize_header(path, start, settings, unit, len(values), rate, continuous, averaged)
    append_digitize_block(path, values, rate, burst)
    return path


def write_digitize_fft(path: Path, start: datetime, settings, unit: str, count: int, rate: float,
                       results=None, continuous: bool = False, averaged: int | None = None) -> Path:
    """
    CSV file of the spectrum of a digitize block of count samples, .csv added
    when it has no suffix; results are services/fft.FftResults, window and
    results in the header. Without results only header and column names: in
    continuous mode the spectrum of each burst follows with
    append_digitize_spectrum(). averaged is the number of bursts for the
    spectrum of their average.
    """
    if not path.suffix:
        path = path.with_suffix(".csv")
    extra_lines = _average_lines(averaged)
    if results is not None:
        extra_lines += [f"FFT window: {results.window_name}", *_fft_result_lines(results)]
    header = _digitize_header(start, settings, unit, count, rate, continuous, extra_lines)
    with open(path, "w", encoding="utf-8", newline="") as file:
        file.write(f"{header}frequency,magnitude\n")
    if results is not None:
        _append_spectrum(path, results)
    return path


def append_digitize_spectrum(path: Path, results, burst: int) -> None:
    """
    Spectrum of a burst at the end of the file, after a '# burst N window X'
    line and a line with its results.
    """
    lines = [f"burst {burst} window {results.window_name}", ", ".join(_fft_result_lines(results))]
    _append_spectrum(path, results, "".join(f"# {line}\n" for line in lines))


def _append_spectrum(path: Path, results, comment: str = "") -> None:
    with open(path, "a", encoding="utf-8", newline="") as file:
        file.write(comment)
        np.savetxt(file, np.column_stack((results.freqs, results.magnitude_db)), fmt="%.12g", delimiter=",")


def _average_lines(averaged: int | None) -> list[str]:
    return [] if averaged is None else [f"Averaged bursts: {averaged}"]


def _fft_result_lines(results) -> list[str]:
    # float: repr of a numpy value is "np.float64(...)"
    return [
        f"Peak: {float(results.peak)!r}",
        f"Peak frequency: {float(results.peak_frequency)!r}",
        f"THD: {float(results.thd_dbc)!r}",
    ]


def _digitize_header(start: datetime, settings, unit: str, count: int, rate: float | None, continuous: bool,
                     extra_lines: list[str] | None = None) -> str:
    lines = [
        SIGNATURE,
        f"Measurement: {_measurement_line('DIGITIZE', settings)}",
        f"Unit: {unit}",
        f"Date time: {start.isoformat(sep=' ', timespec='seconds')}",
        f"Continuous: {'ON' if continuous else 'OFF'}",
        # Of each block in continuous mode
        f"Nrdgs: {count}",
        f"Sample rate: {'unknown' if rate is None else repr(rate)}",
    ]
    lines += extra_lines or []
    return "".join(f"# {line}\n" for line in lines) + "\n"


def statistics_lines(prefix: str, statistics) -> list[str]:
    """
    Statistics lines of the header ('Nrdgs: 58'...), prefix '' or 'Secondary ';
    statistics with count, mean, stdev and stdev_mean, None for no reading.
    """
    def text(value):
        return "" if value is None else repr(value)

    if statistics is None:
        return [f"{prefix}{STATISTICS_KEYS[0]}: 0"] + [f"{prefix}{key}: " for key in STATISTICS_KEYS[1:]]
    values = (statistics.count, text(statistics.mean), text(statistics.stdev), text(statistics.stdev_mean))
    return [f"{prefix}{key}: {value}" for key, value in zip(STATISTICS_KEYS, values)]


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


def _file_range_label(settings, unit: str) -> str:
    """Range in a file name: the range label, which has its unit, 'AUTO_<unit>' in autorange."""
    label = _range_label(settings)
    if label == gui_values.RANGE_MODE_AUTO and unit:
        label = f"{label}_{unit}"
    return label


def _remove_oldest(directory: Path, keep: int) -> None:
    """Delete the files (CSV and PNG) of the oldest acquisitions, keeping the newest `keep`."""
    files = list(directory.glob(_TEMP_GLOB))
    # The names start with date and time: in alphabetical order they are in time order
    stamps = sorted({path.name[:_STAMP_END] for path in files})
    old = set(stamps[: max(len(stamps) - keep, 0)])
    for path in files:
        if path.name[:_STAMP_END] in old:
            path.unlink()
