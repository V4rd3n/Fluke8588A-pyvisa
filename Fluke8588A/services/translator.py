import math

from Fluke8588A.services import translation_tables as tables


class Translator:
    """Translate GUI values (data/gui_values.py) to SCPI values (instrument/scpi.py) and back."""

    def __init__(self):
        """Initialize the translator with mapping dictionaries keyed by parameter type."""
        # GUI → Machine mappings by parameter type
        self._gui_to_machine_maps = tables.GUI_TO_SCPI

        # Machine → GUI mappings by parameter type (reversed); on duplicate
        # machine values the first GUI label wins
        self._machine_to_gui_maps = {}
        for key, gui_map in self._gui_to_machine_maps.items():
            reverse_map = {}
            for gui_value, machine_value in gui_map.items():
                reverse_map.setdefault(machine_value, gui_value)
            self._machine_to_gui_maps[key] = reverse_map

    def translate(self, param_type, gui_value):
        """
        Convert GUI value to machine value based on parameter type.

        Args:
            param_type: A key of translation_tables.GUI_TO_SCPI
            gui_value: The GUI value to translate

        Returns:
            The machine value

        Raises:
            ValueError: If param_type or gui_value has no translation
        """
        mapping = self._gui_to_machine_maps.get(param_type)
        if mapping is None:
            raise ValueError(f"Unknown translation table: {param_type!r}")
        if gui_value not in mapping:
            raise ValueError(f"No {param_type} translation for GUI value {gui_value!r}")
        return mapping[gui_value]

    def translate_resolution(
        self, digits: int, max_digits: int, max_resolution: float
    ) -> float:
        """
        Convert displayed digits to the absolute SCPI resolution.

        Args:
            digits: Displayed digits selected in the GUI
            max_digits: Maximum displayed digits of the function
            max_resolution: Absolute resolution (SI units) of the selected
                range at max_digits

        Returns:
            The absolute resolution to send to the instrument
        """
        if isinstance(max_resolution, str) or max_resolution <= 0:
            raise ValueError(f"Invalid maximum resolution: {max_resolution!r}")
        if not 0 < digits <= max_digits:
            raise ValueError(f"Unsupported resolution digits: {digits}")
        # One digit less means a resolution one decade coarser; round off the
        # float noise of the product so the SCPI string stays clean
        return float(f"{max_resolution * 10 ** (max_digits - digits):.12g}")

    def translate_resolution_from_machine(
        self, resolution_value, max_digits: int, max_resolution: float
    ) -> int:
        """
        Convert the absolute resolution returned by the instrument to displayed digits.

        Args:
            resolution_value: Resolution returned by the instrument (SI units)
            max_digits: Maximum displayed digits of the function
            max_resolution: Absolute resolution (SI units) of the measured
                range at max_digits

        Returns:
            The displayed digits closest to the instrument resolution
        """
        if isinstance(max_resolution, str) or max_resolution <= 0:
            raise ValueError(f"Invalid maximum resolution: {max_resolution!r}")
        value = float(resolution_value)
        if value <= 0 or not math.isfinite(value):
            raise ValueError(
                f"Instrument returned an unsupported resolution: {resolution_value!r}"
            )
        # The instrument may coerce the value, so take the nearest decade
        steps = round(math.log10(value / max_resolution))
        return max(1, min(max_digits, max_digits - steps))

    def translate_from_machine(self, param_type, machine_value):
        """Convert an instrument value to its corresponding GUI value."""
        mapping = self._machine_to_gui_maps.get(param_type, {})
        value = str(machine_value).strip()
        if value in mapping:
            return mapping[value]
        try:
            numeric_value = float(machine_value)
        except (TypeError, ValueError):
            raise ValueError(
                f"Instrument returned an unsupported {param_type} value: "
                f"{machine_value!r}"
            ) from None
        for instrument_value, gui_value in mapping.items():
            try:
                if float(instrument_value) == numeric_value:
                    return gui_value
            except (TypeError, ValueError):
                continue
        raise ValueError(
            f"Instrument returned an unsupported {param_type} value: "
            f"{machine_value!r}"
        )

    '''
    Legacy reverse translation used by the removed instrument readback path.
    def translate_resolution_reverse(self, resolution_value: float) -> int:
        """Convert an absolute SCPI resolution value back to GUI digits."""
        value = float(resolution_value)
        if value.is_integer() and int(value) in scpi.VALID_RESOLUTIONS_DC_DIGITS:
            return int(value)
        for digits in scpi.VALID_RESOLUTIONS_DC_DIGITS:
            if abs(value - 10 ** -digits) < 1e-15:
                return digits
        raise ValueError(f"Invalid absolute resolution value: {resolution_value}")
    
    def translate_reverse(self, param_type, machine_value):
        """
        Convert machine value back to GUI value based on parameter type.
        
        Args:
            param_type: Type of parameter ("zin", "dcv_range", "dci_range", "ohm_range")
            machine_value: The machine value to translate
            
        Returns:
            str: The GUI value, or error_value if not found
        """
        mapping = self._machine_to_gui_maps.get(param_type, {})
        
        #Strip whitespace if string
        machine_value_stripped = str(machine_value).strip()
        
        #Try direct lookup first
        if machine_value_stripped in mapping:
            return mapping[machine_value_stripped]
        if machine_value in mapping:
            return mapping[machine_value]
        
        #Try numeric conversion for range/mode parameters
        if param_type in ["dcv_range", "dci_range", "ohm_range", "ohm_mode"]:
            try:
                numeric_value = float(machine_value_stripped)
                if numeric_value in mapping:
                    return mapping[numeric_value]
            except (ValueError, TypeError):
                pass
        
        return self.error_value
    '''