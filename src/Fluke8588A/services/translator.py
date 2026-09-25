from src.Fluke8588A.data.spin_box_values import *
from src.Fluke8588A.instrument.config import InstrumentConfig as _inst_conf
class Translator:
    def __init__(self):
        """Initialize the translator with mapping dictionaries keyed by parameter type."""
        self.error_value = "NO_TRANS"
        
        # GUI → Machine mappings by parameter type
        self._gui_to_machine_maps = {
            "impedence": dict(zip(DCV_IMPEDENCE, _inst_conf.IMPEDANCES_DCV_VAL)),
            "dcv_range": dict(zip(DCV_RANGE, _inst_conf.DCV_RANGE_VAL)),
            "dci_range": dict(zip(DCI_RANGE, _inst_conf.DCI_RANGE_VAL)),
            "ohm_range": dict(zip(OHM_RANGE, _inst_conf.OHM_RANGE_VAL)),
            "ohm_mode" : dict(zip(OHM_MODES, _inst_conf.OHM_MODES_VAL))
        }
        
        # Machine → GUI mappings by parameter type (reversed)
        self._machine_to_gui_maps = {
            key: {v: k for k, v in gui_map.items()}
            for key, gui_map in self._gui_to_machine_maps.items()
        }
    
    def translate(self, param_type, gui_value):
        """
        Convert GUI value to machine value based on parameter type.
        
        Args:
            param_type: Type of parameter ("zin", "dcv_range", "dci_range", "ohm_range")
            gui_value: The GUI value to translate
            
        Returns:
            str: The machine value, or error_value if not found
        """
        mapping = self._gui_to_machine_maps.get(param_type, {})
        return mapping.get(gui_value, self.error_value)
    
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
    
    def translate_dcv(self, dcv_dict):
        """
        Translate DCV settings from GUI format to machine format.
        
        Args:
            dcv_dict: Dictionary with DCV settings (range_val, zin, etc.)
            
        Returns:
            dict: Translated DCV settings
        """
        return {
            "range_mode": dcv_dict.get("range_mode"),
            "range_val": self.translate("dcv_range", dcv_dict.get("range_val")),
            "resolution": dcv_dict.get("resolution"),
            "zin": self.translate("impedence", dcv_dict.get("zin")),
            "aperture_mode": dcv_dict.get("aperture_mode"),
            "time": dcv_dict.get("time")
        }
    
    def translate_dci(self, dci_dict):
        """
        Translate DCI settings from GUI format to machine format.
        
        Args:
            dci_dict: Dictionary with DCI settings (range_val, etc.)
            
        Returns:
            dict: Translated DCI settings
        """
        return {
            "range_mode": dci_dict.get("range_mode"),
            "range_val": self.translate("dci_range", dci_dict.get("range_val")),
            "resolution": dci_dict.get("resolution"),
            "aperture_mode": dci_dict.get("aperture_mode"),
            "time": dci_dict.get("time")
        }
    
    def translate_ohms(self, ohms_dict):
        """
        Translate OHMS settings from GUI format to machine format.
        
        Args:
            ohms_dict: Dictionary with OHMS settings (range_val, mode, etc.)
            
        Returns:
            dict: Translated OHMS settings
        """
        return {
            "four": ohms_dict.get("four"),
            "range_val": self.translate("ohm_range", ohms_dict.get("range_val")),
            "resolution": ohms_dict.get("resolution"),
            "mode": self.translate("ohm_mode", ohms_dict.get("mode")),
            "filter": ohms_dict.get("filter"),
            "low_i": ohms_dict.get("low_i"),
            "aperture_mode": ohms_dict.get("aperture_mode"),
            "time": ohms_dict.get("time")
        }
    
    def translate_dcv_reverse(self, dcv_dict):
        """
        Translate DCV settings from machine format back to GUI format.
        
        Args:
            dcv_dict: Dictionary with DCV settings in machine format (range_val, zin, etc.)
            
        Returns:
            dict: Translated DCV settings in GUI format
        """
        return {
            "range_mode": dcv_dict.get("range_mode"),
            "range_val": self.translate_reverse("dcv_range", dcv_dict.get("range_val")),
            "resolution": dcv_dict.get("resolution"),
            "zin": self.translate_reverse("impedence", dcv_dict.get("zin")),
            "aperture_mode": dcv_dict.get("aperture_mode"),
            "time": dcv_dict.get("time")
        }
    
    def translate_dci_reverse(self, dci_dict):
        """
        Translate DCI settings from machine format back to GUI format.
        
        Args:
            dci_dict: Dictionary with DCI settings in machine format (range_val, etc.)
            
        Returns:
            dict: Translated DCI settings in GUI format
        """
        return {
            "range_mode": dci_dict.get("range_mode"),
            "range_val": self.translate_reverse("dci_range", dci_dict.get("range_val")),
            "resolution": dci_dict.get("resolution"),
            "aperture_mode": dci_dict.get("aperture_mode"),
            "time": dci_dict.get("time")
        }
    
    def translate_ohms_reverse(self, ohms_dict):
        """
        Translate OHMS settings from machine format back to GUI format.
        
        Args:
            ohms_dict: Dictionary with OHMS settings in machine format (range_val, mode, etc.)
            
        Returns:
            dict: Translated OHMS settings in GUI format
        """
        return {
            "four": ohms_dict.get("four"),
            "range_val": self.translate_reverse("ohm_range", ohms_dict.get("range_val")),
            "resolution": ohms_dict.get("resolution"),
            "mode": self.translate_reverse("ohm_mode", ohms_dict.get("mode")),
            "filter": ohms_dict.get("filter"),
            "low_i": ohms_dict.get("low_i"),
            "aperture_mode": ohms_dict.get("aperture_mode"),
            "time": ohms_dict.get("time")
        }