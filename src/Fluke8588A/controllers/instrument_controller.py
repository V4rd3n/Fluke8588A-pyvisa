from src.Fluke8588A.instrument.Fluke8588A import Fluke8588A
from typing import Optional, TYPE_CHECKING
import logging
from src.Fluke8588A.instrument.config import InstrumentConfig
from src.Fluke8588A.data.settings import DcvSettings, DciSettings, OhmsSettings


class InstrumentController:
    """
    Model layer for instrument control in MVP pattern.
    Provides a clean interface between the Presenter and the Fluke8588A library.
    """
    
    def __init__(self):
        """Initialize the controller without connecting to any instrument."""
        self._instrument: Optional[Fluke8588A] = None
        logging.info("InstrumentController initialized")
    
    def is_connected(self) -> bool:
        """
        Check if instrument is connected.
        
        Returns:
            bool: True if instrument is connected, False otherwise
        """
        return self._instrument is not None and self._instrument.is_connected
    
    def connect(self, address: str) -> None:
        """
        Connect to instrument at given GPIB address.
        
        Args:
            address: GPIB address of the instrument
            
        Raises:
            Exception: If connection fails
        """
        if self.is_connected():
            self.disconnect()
        
        self._instrument = Fluke8588A(address)
        logging.info(f"Connected to instrument at address {address}")
    
    def disconnect(self) -> None:
        """
        Disconnect from instrument and clean up resources.
        """
        if self._instrument is not None:
            self._instrument.close()
            self._instrument = None
            logging.info("Disconnected from instrument")
    
    def read(self) -> str:
        """
        Read measurement from instrument.
        
        Returns:
            str: Measurement value as string
            
        Raises:
            RuntimeError: If not connected to instrument
        """
        if not self.is_connected():
            raise RuntimeError("Cannot read: not connected to instrument")
        
        return self._instrument.read()
    
    def identify(self) -> str:
        """
        Get instrument identification string.
        
        Returns:
            str: IDN string
            
        Raises:
            RuntimeError: If not connected to instrument
        """
        if not self.is_connected():
            raise RuntimeError("Cannot identify: not connected to instrument")
        
        return self._instrument.identify()
    
    def reset(self) -> None:
        """
        Reset instrument to power-on state.
        
        Raises:
            RuntimeError: If not connected to instrument
        """
        if not self.is_connected():
            raise RuntimeError("Cannot reset: not connected to instrument")
        
        self._instrument.reset()
    
    def init_dcv(self, range_mode: str, range_val: float, resolution_val: int, 
                 zin_val: str, aperture_mode: str, time_val: float) -> None:
        """
        Initialize DC voltage measurement mode.
        
        Args:
            range_mode: "AUTO" or "MAN"
            range_val: Range value
            resolution_val: Resolution in digits (4-8)
            zin_val: Input impedance ("AUTO", "1M", or "10M")
            aperture_mode: Aperture mode ("AUTO", "FAST", or "MAN")
            time_val: 0.00001 to 10 seconds
            
        Raises:
            RuntimeError: If not connected to instrument
        """
        if not self.is_connected():
            raise RuntimeError("Cannot initialize DCV: not connected to instrument")
        
        self._instrument.init_dcv(range_mode, range_val, resolution_val, 
                                  zin_val, aperture_mode, time_val)
    
    def write(self, command: str) -> None:
        """
        Write command to instrument.
        
        Args:
            command: SCPI command string
            
        Raises:
            RuntimeError: If not connected to instrument
        """
        if not self.is_connected():
            raise RuntimeError("Cannot write: not connected to instrument")
        
        self._instrument.write(command)
    
    def query(self, command: str) -> str:
        """
        Query instrument (write and read).
        
        Args:
            command: SCPI command string
            
        Returns:
            str: Response from instrument
            
        Raises:
            RuntimeError: If not connected to instrument
        """
        if not self.is_connected():
            raise RuntimeError("Cannot query: not connected to instrument")
        
        return self._instrument.query(command)

    def set(self, mode: str, settings):
        """
        Configure instrument with given settings and return actual values.
        
        Args:
            mode: Measurement mode (e.g., "DCV", "OHMS")
            settings: Settings dataclass with configuration parameters
            
        Returns:
            Settings dataclass: Actual settings read back from the instrument
            
        Raises:
            RuntimeError: If not connected to instrument
        """
        if not self.is_connected():
            raise RuntimeError("Cannot set mode: not connected to instrument")
        
        if mode == "DCV":
            from src.Fluke8588A.data.settings import DcvSettings
            
            root = InstrumentConfig.ROOT_DCV
            
            self._instrument.init_dcv(
                range_mode=settings.range_mode,
                range_val=settings.range_val,
                resolution_val=settings.resolution,
                zin_val=settings.zin,
                aperture_mode=settings.aperture_mode,
                time_val=settings.time
            )
            
            actual_settings = DcvSettings(
                range_mode=self._instrument.getRangeMode(root),
                range_val=str(self._instrument.getRange(root)),
                resolution=int(self._instrument.getResolution(root)),
                zin=self._instrument.getImp(root),
                aperture_mode=self._instrument.getApertureMode(root),
                time=self._instrument.getTime(root)
            )
            
            return actual_settings
        
        elif mode == "OHMS":    
            root= InstrumentConfig.ROOT_RESISTANCE #sets as default
            # Determine range_mode based on range_val
            range_mode = "AUTO" if settings.range_val == "AUTO ON" else "MAN"
            # Convert filter and low_i to instrument format (0 or 1)
            filter_val = 1 if settings.filter else 0
            low_mode_val = 1 if settings.low_i else 0
            
            if settings.four==True:
                root= InstrumentConfig.ROOT_FRESISTANCE
                self._instrument.init_fresistance(
                    aperture_mode=settings.aperture_mode,
                    time_val=float(settings.time),
                    mode_val=settings.mode,
                    low_mode_val=low_mode_val,
                    range_mode=range_mode,
                    range_val=settings.range_val,
                    resolution_val=settings.resolution,
                    filter_val=filter_val
                )

            elif settings.four==False:
                root= InstrumentConfig.ROOT_RESISTANCE
                self._instrument.init_resistance(
                    aperture_mode=settings.aperture_mode,
                    time_val=float(settings.time),
                    mode_val=settings.mode,
                    low_mode_val=low_mode_val,
                    range_mode=range_mode,
                    range_val=settings.range_val,
                    resolution_val=settings.resolution,
                    filter_val=filter_val
                )
                
            actual_settings = OhmsSettings(
                four=settings.four,
                range_val=str(self._instrument.getRange(root)),
                resolution=int(self._instrument.getResolution(root)),
                mode=self._instrument.getWireMode(root),
                filter=self._instrument.getFilter(root),
                low_i=self._instrument.getLowCurrentMode(root),
                aperture_mode=self._instrument.getApertureMode(root),
                time=self._instrument.getTime(root)
            )
            
            return actual_settings
        elif mode == 'DCI':
            from src.Fluke8588A.data.settings import DciSettings
                
            root = InstrumentConfig.ROOT_DCI
            
            self._instrument.init_dci(
                range_mode=settings.range_mode,
                range_val=settings.range_val,
                resolution_val=settings.resolution,
                aperture_mode=settings.aperture_mode,
                time_val=settings.time
            )
            
            actual_settings = DciSettings(
                range_mode=self._instrument.getRangeMode(root),
                range_val=str(self._instrument.getRange(root)),
                resolution=int(self._instrument.getResolution(root)),
                aperture_mode=self._instrument.getApertureMode(root),
                time=self._instrument.getTime(root)
            )
            
            return actual_settings
        
        raise ValueError(f"Invalid mode: {mode}")