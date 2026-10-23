import logging
from typing import Optional  # TYPE_CHECKING unused

import pyvisa

from Fluke8588A.instrument.Fluke8588A import Fluke8588A
from Fluke8588A.instrument import scpi
from Fluke8588A.data.settings import (
    AciSettings,
    AcvSettings,
    DcvSettings,
    DciSettings,
    DigitizeSettings,
    OhmsSettings,
    TriggerBaseSettings,
)


class InstrumentController:
    """
    Model layer for instrument control in MVP pattern.
    Provides a clean interface between the Presenter and the Fluke8588A library.
    """
    
    def __init__(self):
        """Initialize the controller without connecting to any instrument."""
        self._instrument: Optional[Fluke8588A] = None
        logging.info("InstrumentController initialized")

    def scan_resources(self) -> list[dict[str, str]]:
        """Find VISA resources and return display and connection information."""
        resource_manager = pyvisa.ResourceManager()
        resources = []

        try:
            for address in resource_manager.list_resources():
                identity = "No identification response"

                try:
                    instrument = resource_manager.open_resource(address)
                    try:
                        instrument.timeout = scpi.SCAN_TIMEOUT_MS
                        identity = instrument.query("*IDN?").strip()
                    finally:
                        instrument.close()
                except Exception as error:
                    logging.warning("Could not identify VISA resource %s: %s", address, error)

                identity_parts = [part.strip() for part in identity.split(",")]
                if identity != "No identification response":
                    display_identity = ", ".join(identity_parts[:3])
                else:
                    display_identity = identity
                connection_type = address.split("::", 1)[0]

                resources.append({
                    "address": address,
                    "identity": identity,
                    "display_name": f"{display_identity} ({connection_type})",
                })

            return resources
        finally:
            resource_manager.close()
    
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

    def get_line_frequency(self) -> float:
        """Return the connected instrument's power-line frequency in hertz."""
        if not self.is_connected():
            raise RuntimeError("Cannot get line frequency: not connected to instrument")

        return self._instrument.get_line_frequency()

    def reset_trigger_base(self) -> None:
        """Reset the instrument's base-trigger subsystem."""
        if not self.is_connected():
            raise RuntimeError("Cannot reset trigger base: not connected to instrument")
        self._instrument.resetTrigger(scpi.ROOT_TRIGGER)

    # TODO: This is a test and should be reworked with a setTrigger in the Fluke8588A class
    def set_trigger_base(self, settings: TriggerBaseSettings) -> None:
        """Apply base-trigger settings (SCPI values) to the connected instrument."""
        if not self.is_connected():
            raise RuntimeError("Cannot set trigger base: not connected to instrument")

        root = scpi.ROOT_TRIGGER
        self._instrument.setSource(root, settings.source)
        self._instrument.setCount(root, settings.count)
        self._instrument.setEcount(root, settings.ecount)
        self._instrument.setDelayMode(root, settings.delay_auto)
        self._instrument.setDelay(root, settings.delay)
        self._instrument.setHoldoffAuto(root, settings.holdoff_auto)
        self._instrument.setHoldoff(root, settings.holdoff)
        if settings.source == scpi.TRIGGER_SOURCE_TIMER:
            self._instrument.setTimer(root, settings.timer)
        if settings.source == scpi.TRIGGER_SOURCE_EXTERNAL:
            self._instrument.setExternal(root, settings.ext_edge)
        if settings.source == scpi.TRIGGER_SOURCE_INTERNAL:
            self._instrument.setCoupling(root, settings.sig_coupling)
            self._instrument.setSlope(root, settings.sig_slope)
            self._instrument.setLevel(root, settings.sig_level)
            self._instrument.setFilter(root, settings.sig_filter)
    
    def reset(self) -> None:
        """
        Reset instrument to power-on state.
        
        Raises:
            RuntimeError: If not connected to instrument
        """
        if not self.is_connected():
            raise RuntimeError("Cannot reset: not connected to instrument")
        
        self._instrument.reset()
    
    def set_dcv(self, settings: DcvSettings) -> DcvSettings:
        """Configure DC voltage and return the values accepted by the instrument."""
        if not self.is_connected():
            raise RuntimeError("Cannot set DCV: not connected to instrument")

        actual = self._instrument.set_dcv(
            range_mode=settings.range_mode,
            range_val=settings.range_val,
            resolution_val=settings.resolution,
            zin_val=settings.zin,
            aperture_mode=settings.aperture_mode,
            time_val=settings.time,
        )
        return DcvSettings(**actual)

    def set_dci(self, settings: DciSettings) -> DciSettings:
        """Configure DC current and return the values accepted by the instrument."""
        if not self.is_connected():
            raise RuntimeError("Cannot set DCI: not connected to instrument")

        actual = self._instrument.set_dci(
            range_mode=settings.range_mode,
            range_val=settings.range_val,
            resolution_val=settings.resolution,
            aperture_mode=settings.aperture_mode,
            time_val=settings.time,
        )
        return DciSettings(**actual)

    def set_acv(self, settings: AcvSettings) -> AcvSettings:
        """Configure AC voltage and return the values accepted by the instrument."""
        if not self.is_connected():
            raise RuntimeError("Cannot set ACV: not connected to instrument")

        actual = self._instrument.set_acv(
            range_mode=settings.range_mode,
            range_val=settings.range_val,
            resolution_val=settings.resolution,
            bandwidth=settings.bandwidth,
            filter_val=settings.rms_filter,
            coupling_signal=settings.coupling_impedance,
            counter_coupling=settings.frequency_path_coupling,
            counter_blimit=settings.frequency_path_bandwidth_limit,
            counter_gate=settings.counter_gate,
            secondary=settings.secondary_reading,
            secondary_method=settings.peak_to_peak,
        )
        return AcvSettings(**actual)

    def set_aci(self, settings: AciSettings) -> AciSettings:
        """Configure AC current and return the values accepted by the instrument."""
        if not self.is_connected():
            raise RuntimeError("Cannot set ACI: not connected to instrument")

        actual = self._instrument.set_aci(
            range_mode=settings.range_mode,
            range_val=settings.range_val,
            resolution_val=settings.resolution,
            filter_val=settings.rms_filter,
            coupling_signal=settings.signal_path_coupling,
            counter_coupling=settings.frequency_path_coupling,
            counter_blimit=settings.frequency_path_bandwidth_limit,
            counter_gate=settings.counter_gate,
            secondary=settings.secondary_reading,
            secondary_method=settings.peak_to_peak,
        )
        return AciSettings(**actual)

    def set_ohms(self, settings: OhmsSettings) -> OhmsSettings:
        """Configure 2-wire/4-wire resistance and return the values accepted by the instrument."""
        if not self.is_connected():
            raise RuntimeError("Cannot set OHMS: not connected to instrument")

        actual = self._instrument.set_ohms(
            measurement=settings.mode,
            range_mode=settings.range_mode,
            range_val=settings.range_val,
            resolution_val=settings.resolution,
            filter_val=settings.filter,
            low_current=settings.low_current,
            aperture_mode=settings.aperture_mode,
            time_val=settings.time,
        )
        return OhmsSettings(**actual)

    def set_digitize(self, settings: DigitizeSettings) -> DigitizeSettings:
        """Configure digitize voltage/current and return the values accepted by the instrument."""
        if not self.is_connected():
            raise RuntimeError("Cannot set DIGITIZE: not connected to instrument")

        actual = self._instrument.set_digitize(
            measurement=settings.signal,
            range_val=settings.range_val,
            coupling=settings.coupling_impedance,
            filter_val=settings.filter,
            aperture=settings.aperture,
        )
        return DigitizeSettings(**actual)

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

    '''
    Legacy generic SET/readback path. Active measurement methods configure
    the instrument without querying it for accepted values.
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
            from Fluke8588A.data.settings import DcvSettings
            
            root = scpi.ROOT_DCV
            
            self.set_dcv(settings)
            
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
            root= scpi.ROOT_RESISTANCE #sets as default
            # Determine range_mode based on range_val
            range_mode = "AUTO" if settings.range_val == "AUTO ON" else "MAN"
            # Convert filter and low_i to instrument format (0 or 1)
            filter_val = 1 if settings.filter else 0
            low_mode_val = 1 if settings.low_i else 0
            
            if settings.four==True:
                root= scpi.ROOT_FRESISTANCE
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
                root= scpi.ROOT_RESISTANCE
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
            from Fluke8588A.data.settings import DciSettings
                
            root = scpi.ROOT_DCI
            
            self.set_dci(settings)
            
            actual_settings = DciSettings(
                range_mode=self._instrument.getRangeMode(root),
                range_val=str(self._instrument.getRange(root)),
                resolution=int(self._instrument.getResolution(root)),
                aperture_mode=self._instrument.getApertureMode(root),
                time=self._instrument.getTime(root)
            )
            
            return actual_settings
        
        raise ValueError(f"Invalid mode: {mode}")
    '''