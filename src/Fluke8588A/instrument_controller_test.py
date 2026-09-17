## TESTER TO BE USED IF NOT ABLE TO CONNECT TO MACHINE
from typing import Optional
import logging
import random
import time
from src.Fluke8588A.config import InstrumentConfig
from src.Fluke8588A.data.settings import DcvSettings

class InstrumentControllerTest:
    """
    Test/Mock version of InstrumentController for testing without hardware.
    Prints all actions instead of communicating with actual instrument.
    """
    
    def __init__(self):
        """Initialize the test controller without connecting to any instrument."""
        self._is_connected: bool = False
        self._address: Optional[str] = None
        # Mock instrument state
        self._mock_state = {
            'range_mode': 'AUTO',
            'range_val': '10.0',
            'resolution': 6,
            'zin': '10M',
            'aperture_mode': 'AUTO',
            'time': 1.0
        }
        logging.info("InstrumentControllerTest initialized (MOCK MODE)")
        print("[TEST] InstrumentControllerTest initialized (no hardware)")
    
    def is_connected(self) -> bool:
        """
        Check if instrument is connected.
        
        Returns:
            bool: True if instrument is connected, False otherwise
        """
        print(f"[TEST] Checking connection status: {self._is_connected}")
        return self._is_connected
    
    def connect(self, address: str) -> None:
        """
        Connect to instrument at given GPIB address.
        
        Args:
            address: GPIB address of the instrument
        """
        if self.is_connected():
            print(f"[TEST] Already connected to address {self._address}, disconnecting first...")
            self.disconnect()
        
        print(f"[TEST] Connecting to instrument at GPIB address: {address}")
        print(f"[TEST] Would open: {InstrumentConfig.GPIB_PREFIX}{address}{InstrumentConfig.GPIB_SUFFIX}")
        self._address = address
        self._is_connected = True
        logging.info(f"TEST: Connected to mock instrument at address {address}")
        print(f"[TEST] Successfully connected!")
    
    def disconnect(self) -> None:
        """
        Disconnect from instrument and clean up resources.
        """
        if self._is_connected:
            print(f"[TEST] Disconnecting from instrument at address {self._address}")
            self._is_connected = False
            self._address = None
            logging.info("TEST: Disconnected from mock instrument")
            print("[TEST] Successfully disconnected!")
        else:
            print("[TEST] Already disconnected")
    
    def read(self) -> str:
        """
        Read measurement from instrument.
        
        Returns:
            str: Measurement value as string
            
        Raises:
            RuntimeError: If not connected to instrument
        """
        if not self.is_connected():
            print("[TEST] ERROR: Cannot read - not connected to instrument")
            raise RuntimeError("Cannot read: not connected to instrument")
        
        mock_value = "+1.234567E+00"
        print(f"[TEST] Reading measurement from instrument...")
        print(f"[TEST] Would send: :READ?")
        print(f"[TEST] Mock response: {mock_value}")
        return mock_value
    
    def identify(self) -> str:
        """
        Get instrument identification string.
        
        Returns:
            str: IDN string
            
        Raises:
            RuntimeError: If not connected to instrument
        """
        if not self.is_connected():
            print("[TEST] ERROR: Cannot identify - not connected to instrument")
            raise RuntimeError("Cannot identify: not connected to instrument")
        
        mock_idn = "FLUKE,8588A,12345678,1.0.0.0"
        print(f"[TEST] Getting instrument identification...")
        print(f"[TEST] Would send: *IDN?")
        print(f"[TEST] Mock response: {mock_idn}")
        return mock_idn
    
    def reset(self) -> None:
        """
        Reset instrument to power-on state.
        
        Raises:
            RuntimeError: If not connected to instrument
        """
        if not self.is_connected():
            print("[TEST] ERROR: Cannot reset - not connected to instrument")
            raise RuntimeError("Cannot reset: not connected to instrument")
        
        print("[TEST] Resetting instrument to power-on state...")
        print("[TEST] Would send: *RST")
        # Reset mock state to defaults
        self._mock_state = {
            'range_mode': 'AUTO',
            'range_val': '10.0',
            'resolution': 6,
            'zin': '10M',
            'aperture_mode': 'AUTO',
            'time': 1.0
        }
        print("[TEST] Reset complete!")
    
    def init_dcv(self, range_mode: str, range_val: float, resolution_val: int, 
                 zin: str, aperture_mode: str, time: float) -> None:
        """
        Initialize DC voltage measurement mode.
        
        Args:
            range_mode: "AUTO" or "MAN"
            range_val: Range value
            resolution_val: Resolution in digits (4-8)
            zin: Input impedance ("AUTO", "1M", or "10M")
            aperture_mode: Aperture mode ("AUTO", "FAST", or "MAN")
            time: aperture time  value (0.000001 to 10)
            
        Raises:
            RuntimeError: If not connected to instrument
        """
        if not self.is_connected():
            print("[TEST] ERROR: Cannot initialize DCV - not connected to instrument")
            raise RuntimeError("Cannot initialize DCV: not connected to instrument")
        
        print("[TEST] Initializing DC Voltage mode with parameters:")
        print(f"[TEST]   Range Mode: {range_mode}")
        print(f"[TEST]   Range Value: {range_val}")
        print(f"[TEST]   Resolution: {resolution_val} digits")
        print(f"[TEST]   Input Impedance: {zin}")
        print(f"[TEST]   Aperture Mode: {aperture_mode}")
        print(f"[TEST]   Time: {time}")
        print(f"[TEST] Would send: :FUNC \"{InstrumentConfig.ROOT_DCV}\"")
        print(f"[TEST] Would send: {InstrumentConfig.ROOT_DCV}:RANG:AUTO {1 if range_mode == 'AUTO' else 0}")
        print(f"[TEST] Would send: {InstrumentConfig.ROOT_DCV}:RANG {range_val}")
        print(f"[TEST] Would send: {InstrumentConfig.ROOT_DCV}:RES {10**(-resolution_val)}")
        print(f"[TEST] Would send: {InstrumentConfig.ROOT_DCV}:IMP {zin}")
        print(f"[TEST] Would send: {InstrumentConfig.ROOT_DCV}:APER:MODE {aperture_mode}")
        print(f"[TEST] Would send: {InstrumentConfig.ROOT_DCV}:APER {time}")
        
        # Update mock state
        self._mock_state['range_mode'] = range_mode
        self._mock_state['range_val'] = str(range_val)
        self._mock_state['resolution'] = resolution_val
        self._mock_state['zin'] = zin
        self._mock_state['aperture_mode'] = aperture_mode
        self._mock_state['time'] = time
        print("[TEST] DCV initialization complete!")
    
    def write(self, command: str) -> None:
        """
        Write command to instrument.
        
        Args:
            command: SCPI command string
            
        Raises:
            RuntimeError: If not connected to instrument
        """
        if not self.is_connected():
            print("[TEST] ERROR: Cannot write - not connected to instrument")
            raise RuntimeError("Cannot write: not connected to instrument")
        
        print(f"[TEST] Writing command: {command}")
    
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
            print("[TEST] ERROR: Cannot query - not connected to instrument")
            raise RuntimeError("Cannot query: not connected to instrument")
        
        print(f"[TEST] Querying: {command}")
        
        # Return mock responses based on command
        if "*IDN?" in command:
            return "FLUKE,8588A,12345678,1.0.0.0"
        elif ":READ?" in command:
            mock_value = random.uniform(0, 1.005)
            return f"+{mock_value:.6E}"
        elif "FETCh?" in command or "FETCH?" in command:
            # Continuous reading — simulate small noise around 1V
            time.sleep(0.1)
            mock_value = random.uniform(0, 1.005)
            return f"+{mock_value:.6E}"
        else:
            return "OK"

    def set(self, mode: str, settings):
        """
        Configure instrument with given settings and return actual values.
        
        Args:
            mode: Measurement mode (e.g., "DCV")
            settings: Settings dataclass with configuration parameters
            
        Returns:
            DcvSettings: Actual settings read back from the instrument
            
        Raises:
            RuntimeError: If not connected to instrument
        """
        print("\n" + "="*60)
        print(f"[TEST] *** SET METHOD CALLED - Mode: {mode} ***")
        print("="*60)
        
        if not self.is_connected():
            print("[TEST] ERROR: Cannot set mode - not connected to instrument")
            raise RuntimeError("Cannot set mode: not connected to instrument")
        
        if mode == "DCV":
            print(f"[TEST] Setting DCV mode with settings:")
            print(f"[TEST]   Range Mode: {settings.range_mode}")
            print(f"[TEST]   Range Value: {settings.range_val}")
            print(f"[TEST]   Resolution: {settings.resolution}")
            print(f"[TEST]   Input Z: {settings.zin}")
            print(f"[TEST]   Aperture: {settings.aperture_mode}")            
            print(f"[TEST]   Time: {settings.time}")
            
            # Call init_dcv
            self.init_dcv(
                range_mode=settings.range_mode,
                range_val=settings.range_val,
                resolution_val=settings.resolution,
                zin=settings.zin,
                aperture_mode="AUTO",  # TO CHANGE
                time=settings.time
            )
            
            print("[TEST] Reading back actual settings from instrument...")
            # Return mock actual settings based on what was set
            actual_settings = DcvSettings(
                range_mode=self._mock_state['range_mode'],
                range_val=self._mock_state['range_val'],
                resolution=self._mock_state['resolution'],
                zin=self._mock_state['zin'],
                aperture_mode=self._mock_state['aperture_mode'],
                time=self._mock_state['time']
            )
            
            print(f"[TEST] Actual settings from instrument: {actual_settings}")
            return actual_settings
        else:
            print(f"[TEST] Unknown mode: {mode}")
            raise ValueError(f"Unknown mode: {mode}")