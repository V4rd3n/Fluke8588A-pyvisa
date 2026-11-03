"""
Files of services/measurement_file read back: a measurement file with its
readings and statistics (repaired in the file when missing or wrong), a
digitize file with its blocks and spectra. The format belongs to
measurement_file, which writes it.
"""
from dataclasses import dataclass
from pathlib import Path
from Fluke8588A.data import gui_values
from Fluke8588A.services.measurement_file import (
    SIGNATURE,
    STATISTICS_KEYS,
    digitize_frequency_name,
    statistics_lines,
)
from Fluke8588A.services.statistics import RunningStatistics
import numpy as np
import os
import re

# key=value settings of the Measurement line, the values may have spaces ("AC, 1MΩ")
_SETTING_PATTERN = re.compile(r"(\w+)=(.*?)(?= \w+=|$)")


class NotMeasurementFileError(ValueError):
    """The file was not written by the program, or nothing of it can be read."""


class UnsupportedMeasurementError(ValueError):
    """A file of the program of another kind than the one asked (digitize or not)."""


@dataclass(frozen=True)
class ReadingStatistics:
    count: int
    last: float | None
    mean: float | None
    stdev: float | None
    stdev_mean: float | None


@dataclass(frozen=True)
class LoadedMeasurement:
    """
    A measurement file read back: function, range label ('1 V', 'AUTO') and
    settings from the Measurement line, units from the Unit line ('' when
    missing), readings without the overloads and their statistics.
    """
    function: str
    range_label: str
    settings: dict[str, str]
    units: tuple[str, ...]
    date_time: str
    times: list[float]
    values: list[float]
    statistics: ReadingStatistics
    secondary_times: list[float] | None
    secondary_values: list[float] | None
    secondary_statistics: ReadingStatistics | None
    # The statistics of the header were missing or wrong, computed from the readings
    repaired: bool


@dataclass(frozen=True)
class DigitizeBurst:
    """
    A block of a digitize file, number None out of continuous mode: its
    samples (empty for a spectrum file read alone), its spectrum and results
    (None when the spectrum file has none for it).
    """
    number: int | None
    x: np.ndarray
    values: np.ndarray
    freqs: np.ndarray | None = None
    magnitude_db: np.ndarray | None = None
    window_name: str | None = None
    peak: float | None = None
    peak_frequency: float | None = None
    thd_dbc: float | None = None


@dataclass(frozen=True)
class LoadedDigitize:
    """
    A digitize samples file read back with its spectrum file, when found
    (digitize_frequency_name()): x is the time in s, the sample number when
    the sample rate is unknown (None). A spectrum file read alone
    (spectrum_only) has the spectra only, samples is the number of samples
    of each block (Nrdgs).
    """
    spectrum_only: bool
    samples: int | None
    range_label: str
    settings: dict[str, str]
    unit: str
    date_time: str
    continuous: bool
    sample_rate: float | None
    bursts: list[DigitizeBurst]
    spectrum_path: Path | None
    # Why the spectrum file was not read, None when read or not there
    spectrum_error: str | None


@dataclass(frozen=True)
class _FileText:
    """Text of a file of the program split in header and rows."""
    text: str
    lines: list[str]
    columns_index: int
    header_lines: list[str]
    header: dict[str, str]
    columns: list[str]

    @property
    def rows(self) -> list[str]:
        """Rows and comment lines after the column names, a last row cut while writing left out."""
        rows = self.lines[self.columns_index + 1:]
        # Each row is written with its newline: without one the last row was cut while writing
        if rows and not self.text.endswith(("\n", "\r")):
            rows = rows[:-1]
        return rows

    @property
    def is_digitize(self) -> bool:
        # Only the digitize files have the Continuous line; the function too,
        # for the files written before it and the damaged ones
        measurement = self.header.get("Measurement", "").split()
        return "Continuous" in self.header or measurement[:1] == ["DIGITIZE"]


def read_file(path: Path) -> LoadedMeasurement | LoadedDigitize:
    """
    Read a file of the program: read_digitize() for the files of a digitize
    acquisition (header with the Continuous line), read_measurement() for the
    other functions.

    Raises NotMeasurementFileError for a file not written by the program.
    """
    file_text = _read_text(path)
    if file_text.is_digitize:
        return _read_digitize(path, file_text)
    return _read_measurement(path, file_text)


def read_measurement(path: Path) -> LoadedMeasurement:
    """
    Read a file of a measurement function (DCV, DCI, ACV, ACI, OHMS). The
    statistics are taken from the header; when they are missing or do not
    match the readings (acquisition interrupted, file damaged) they are
    computed from the readings and the header is rewritten with them, as
    MeasurementFile.close() would have written it.
    """
    file_text = _read_text(path)
    if file_text.is_digitize:
        raise UnsupportedMeasurementError("file of a digitize acquisition")
    return _read_measurement(path, file_text)


def read_digitize(path: Path) -> LoadedDigitize:
    """
    Read the samples file of a digitize acquisition, each block with its
    spectrum and results from the spectrum file next to it, if any; a
    spectrum file alone, with its spectra only.
    """
    file_text = _read_text(path)
    if not file_text.is_digitize:
        raise UnsupportedMeasurementError("not a file of a digitize acquisition")
    return _read_digitize(path, file_text)


def _read_text(path: Path) -> _FileText:
    try:
        with open(path, encoding="utf-8-sig", newline="") as file:
            text = file.read()
    except UnicodeDecodeError:
        raise NotMeasurementFileError("not a text file") from None
    lines = text.splitlines()
    if not lines or lines[0].strip() != f"# {SIGNATURE}":
        raise NotMeasurementFileError(f"the first line is not '# {SIGNATURE}'")
    columns_index = next((i for i, line in enumerate(lines) if line.strip() and not line.startswith("#")), None)
    if columns_index is None:
        raise NotMeasurementFileError("no column names nor readings")
    header_lines = [line[1:].strip() for line in lines[:columns_index] if line.startswith("#")]
    header = {}
    for line in header_lines:
        key, separator, value = line.partition(":")
        if separator:
            header[key.strip()] = value.strip()
    columns = [name.strip() for name in lines[columns_index].split(",")]
    return _FileText(text, lines, columns_index, header_lines, header, columns)


def _read_digitize(path: Path, file_text: _FileText) -> LoadedDigitize:
    header = file_text.header
    _, range_label, settings = _parse_measurement_line(header.get("Measurement", ""))
    try:
        rate = float(header.get("Sample rate", ""))
    except ValueError:
        # 'unknown' when the trigger does not give it
        rate = None
    spectrum_only = file_text.columns[0] == "frequency"
    spectrum_path = None
    spectrum_error = None
    if spectrum_only:
        empty = np.empty(0)
        bursts = [DigitizeBurst(number, empty, empty, **spectrum) for number, spectrum in _spectra(file_text).items()]
    else:
        spectra = {}
        candidate = digitize_frequency_name(path)
        if candidate.exists():
            try:
                spectra = _read_spectra(candidate)
                spectrum_path = candidate
            except (OSError, ValueError) as error:
                spectrum_error = str(error)
        bursts = [
            DigitizeBurst(number, table[:, 0], table[:, 1], **spectra.get(number, {}))
            for number, _, table in _read_sections(file_text.rows, len(file_text.columns))
        ]
    try:
        samples = int(header.get("Nrdgs", ""))
    except ValueError:
        samples = None
    return LoadedDigitize(
        spectrum_only=spectrum_only,
        samples=samples,
        range_label=range_label,
        settings=settings,
        unit=header.get("Unit", "").split(",")[0].strip(),
        date_time=header.get("Date time", ""),
        continuous=header.get("Continuous", "").upper() == "ON",
        sample_rate=rate,
        bursts=bursts,
        spectrum_path=spectrum_path,
        spectrum_error=spectrum_error,
    )


def _read_spectra(path: Path) -> dict[int | None, dict]:
    """Spectra of the spectrum file of a samples file, as _spectra()."""
    file_text = _read_text(path)
    if not file_text.is_digitize or file_text.columns[0] != "frequency":
        raise NotMeasurementFileError("not the spectrum file of a digitize acquisition")
    return _spectra(file_text)


def _spectra(file_text: _FileText) -> dict[int | None, dict]:
    """
    Spectra of a digitize spectrum file by burst number (None for the single
    block), each as the DigitizeBurst fields: window and results from the
    header for a single block, from the comment lines of each burst in
    continuous mode.
    """
    spectra = {}
    for number, comments, table in _read_sections(file_text.rows, len(file_text.columns)):
        if number is None:
            results = dict(file_text.header)
            window_name = results.get("FFT window")
        else:
            # '# burst N window X' then '# Peak: ..., Peak frequency: ..., THD: ...'
            window_name = comments[0].partition(" window ")[2] or None
            results = {}
            for comment in comments[1:]:
                for part in comment.split(","):
                    key, _, value = part.partition(":")
                    results[key.strip()] = value.strip()
        spectra[number] = {
            "freqs": table[:, 0],
            "magnitude_db": table[:, 1],
            "window_name": window_name,
            "peak": _float_or_none(results.get("Peak")),
            "peak_frequency": _float_or_none(results.get("Peak frequency")),
            "thd_dbc": _float_or_none(results.get("THD")),
        }
    return spectra


_BURST_PATTERN = re.compile(r"burst (\d+)\b")


def _read_sections(rows: list[str], column_count: int) -> list[tuple[int | None, list[str], np.ndarray]]:
    """
    Blocks of rows of a digitize file: each '# burst N' line starts a new
    one, the rows before the first are the single block (number None). Every
    block with its comment lines and its rows as an array, damaged rows left
    out.
    """
    sections = []
    number, comments, block = None, [], []
    for row in rows:
        if row.startswith("#"):
            comment = row[1:].strip()
            match = _BURST_PATTERN.match(comment)
            if match:
                if block or number is not None:
                    sections.append((number, comments, block))
                number, comments, block = int(match.group(1)), [comment], []
            else:
                comments.append(comment)
        elif row.strip():
            block.append(row)
    if block or number is not None:
        sections.append((number, comments, block))
    return [(number, comments, _table(block, column_count)) for number, comments, block in sections]


def _table(rows: list[str], column_count: int) -> np.ndarray:
    """Rows of numbers as an array of column_count columns, the damaged ones left out."""
    if not rows:
        return np.empty((0, column_count))
    try:
        table = np.loadtxt(rows, delimiter=",", ndmin=2)
        if table.shape[1] == column_count:
            return table
    except ValueError:
        pass
    # Slow path, only for a damaged file
    table = []
    for row in rows:
        cells = row.split(",")
        if len(cells) != column_count:
            continue
        try:
            table.append([float(cell) for cell in cells])
        except ValueError:
            continue
    return np.array(table, dtype=float).reshape(-1, column_count)


def _float_or_none(text: str | None) -> float | None:
    try:
        return float(text)
    except (TypeError, ValueError):
        return None


def _read_measurement(path: Path, file_text: _FileText) -> LoadedMeasurement:
    header = file_text.header
    function, range_label, settings = _parse_measurement_line(header.get("Measurement", ""))
    columns = file_text.columns
    secondary = "secvalue" in columns
    times, values, secondary_times, secondary_values = _read_rows(file_text.rows, len(columns), secondary)
    text, columns_index, header_lines = file_text.text, file_text.columns_index, file_text.header_lines

    statistics, repaired = _checked_statistics(header, "", values)
    secondary_statistics = None
    if secondary:
        secondary_statistics, secondary_repaired = _checked_statistics(header, "Secondary ", secondary_values)
        repaired = repaired or secondary_repaired
    if repaired:
        _rewrite_statistics(path, text, columns_index, header_lines, statistics, secondary_statistics)
    return LoadedMeasurement(
        function=function,
        range_label=range_label,
        settings=settings,
        units=tuple(unit.strip() for unit in header.get("Unit", "").split(",")),
        date_time=header.get("Date time", ""),
        times=times,
        values=values,
        statistics=statistics,
        secondary_times=secondary_times if secondary else None,
        secondary_values=secondary_values if secondary else None,
        secondary_statistics=secondary_statistics,
        repaired=repaired,
    )


def _parse_measurement_line(line: str) -> tuple[str, str, dict[str, str]]:
    """'ACV 1 V 6 digits rms_filter=40Hz ...' -> ('ACV', '1 V', {'rms_filter': '40Hz', ...})."""
    first_setting = _SETTING_PATTERN.search(line)
    main = (line[: first_setting.start()] if first_setting else line).split()
    settings = {key: value.strip() for key, value in _SETTING_PATTERN.findall(line)}
    function = main[0] if main else ""
    if len(main) > 1 and main[1] == gui_values.RANGE_MODE_AUTO:
        range_label = gui_values.RANGE_MODE_AUTO
    else:
        range_label = " ".join(main[1:3])
    return function, range_label, settings


def _read_rows(rows: list[str], column_count: int, secondary: bool):
    """Times and values of the rows, overloads and damaged rows (cells missing, not numbers) left out."""
    times, values, secondary_times, secondary_values = [], [], [], []
    for row in rows:
        cells = row.split(",")
        if len(cells) != column_count:
            continue
        try:
            elapsed = float(cells[1])
        except (IndexError, ValueError):
            continue
        columns = [(2, times, values)]
        if secondary:
            columns.append((3, secondary_times, secondary_values))
        for index, x, y in columns:
            try:
                value = float(cells[index])
            except (IndexError, ValueError):
                continue
            x.append(elapsed)
            y.append(value)
    return times, values, secondary_times, secondary_values


def _checked_statistics(header: dict[str, str], prefix: str, values: list[float]) -> tuple[ReadingStatistics, bool]:
    """
    Statistics of the header when complete and of the same number of
    readings, otherwise computed from the readings; True when computed.
    """
    computed = RunningStatistics()
    for value in values:
        computed.add(value)
    last = values[-1] if values else None
    from_readings = ReadingStatistics(computed.count, last, computed.mean, computed.stdev, computed.stdev_mean)
    try:
        count = int(header[f"{prefix}Nrdgs"])
        mean, stdev, stdev_mean = (_optional_float(header[f"{prefix}{key}"]) for key in STATISTICS_KEYS[1:])
    except (KeyError, ValueError):
        return from_readings, True
    # Empty in the header only when the readings are too few to compute them
    for value, expected in ((mean, computed.mean), (stdev, computed.stdev), (stdev_mean, computed.stdev_mean)):
        if (value is None) != (expected is None):
            return from_readings, True
    if count != computed.count:
        return from_readings, True
    return ReadingStatistics(count, last, mean, stdev, stdev_mean), False


def _optional_float(text: str) -> float | None:
    return float(text) if text else None


def _rewrite_statistics(path: Path, text: str, columns_index: int, header_lines: list[str],
                        statistics: ReadingStatistics, secondary_statistics: ReadingStatistics | None) -> None:
    """
    Header with the statistics given in place of the old ones, the rows as
    they are: a cut last row stays without its newline, left out again on
    the next read.
    """
    statistics_keys = {f"{prefix}{key}" for prefix in ("", "Secondary ") for key in STATISTICS_KEYS}
    kept = [line for line in header_lines if line.partition(":")[0].strip() not in statistics_keys]
    new_lines = kept + statistics_lines("", statistics)
    if secondary_statistics is not None:
        new_lines += statistics_lines("Secondary ", secondary_statistics)
    temp_path = path.with_suffix(".tmp")
    with open(temp_path, "w", encoding="utf-8", newline="") as file:
        file.write("".join(f"# {line}\n" for line in new_lines) + "\n")
        file.writelines(text.splitlines(keepends=True)[columns_index:])
        file.flush()
        os.fsync(file.fileno())
    os.replace(temp_path, path)
