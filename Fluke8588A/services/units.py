"""Units of the GUI range labels (data/gui_values.py), for showing readings."""

# Multipliers of the SI prefixes used in the range labels; both micro signs
SI_PREFIXES = {"n": 1e-9, "μ": 1e-6, "µ": 1e-6, "m": 1e-3, "": 1.0, "k": 1e3, "M": 1e6, "G": 1e9}


def range_unit(range_label: str, base_unit: str) -> tuple[str, float] | None:
    """
    Unit of a range label and the scale from the base unit to it:
    ("100 mV", "V") -> ("mV", 1e3), value_in_unit = value * scale.

    Returns None when the label has no unit (AUTO).
    """
    parts = range_label.split()
    if len(parts) != 2 or not parts[1].endswith(base_unit):
        return None
    unit = parts[1]
    prefix = unit[: -len(base_unit)]
    if prefix not in SI_PREFIXES:
        return None
    return unit, 1.0 / SI_PREFIXES[prefix]


# Quantity and unit of the AC secondary readings (gui_values.AC_SECONDARY_READING
# names): the peaks are in the unit of the primary reading, crest factor has none
_AC_SECONDARY_UNITS = {
    "Frequency": ("Frequency", "Hz"),
    "Period": ("Period", "s"),
    "Crest factor": ("Crest factor", ""),
}
_AC_SECONDARY_PEAKS = {
    "Pk to Pk": "Peak to peak",
    "Positive peak": "Positive peak",
    "Negative peak": "Negative peak",
}


def ac_secondary_unit(secondary_reading: str, primary_unit: str) -> tuple[str, str]:
    """
    Quantity and base unit of an AC secondary reading:
    ("Frequency", "V") -> ("Frequency", "Hz"), ("Pk to Pk", "A") -> ("Peak to peak", "A").
    """
    if secondary_reading in _AC_SECONDARY_PEAKS:
        return _AC_SECONDARY_PEAKS[secondary_reading], primary_unit
    return _AC_SECONDARY_UNITS.get(secondary_reading, (secondary_reading, ""))
