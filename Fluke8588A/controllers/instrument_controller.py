import logging
from dataclasses import replace
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
    TriggerAdvancedSettings,
    TriggerBaseSettings,
    TriggerLayerHoldoffSettings,
    TriggerLayerSettings,
    TriggerSignalSettings,
)

logger = logging.getLogger(__name__)


class InstrumentController:
    """
    Model layer for instrument control in MVP pattern.
    Provides a clean interface between the Presenter and the Fluke8588A library.
    """
    
    def __init__(self):
        """Initialize the controller without connecting to any instrument."""
        self._instrument: Optional[Fluke8588A] = None
        logger.info("InstrumentController initialized")

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
                    logger.warning("Could not identify VISA resource %s: %s", address, error)

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
        logger.info(f"Connected to instrument at address {address}")
    
    def disconnect(self) -> None:
        """
        Disconnect from instrument and clean up resources.
        """
        if self._instrument is not None:
            self._instrument.close()
            self._instrument = None
            logger.info("Disconnected from instrument")
    
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

    def read_with_secondary(self) -> tuple[str, str | None]:
        """
        Read primary and secondary measurement (same number of readings).

        Returns:
            tuple: primary text, secondary text (None in continuous mode)
        """
        if not self.is_connected():
            raise RuntimeError("Cannot read: not connected to instrument")

        return self._instrument.read_with_secondary()

    def discard_readings(self) -> None:
        """Forget the readings taken so far in continuous mode (INIT:CONT ON)."""
        if not self.is_connected():
            raise RuntimeError("Cannot discard readings: not connected to instrument")
        self._instrument.discard_readings()
    
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

    def set_trigger_base(self, settings: TriggerBaseSettings) -> TriggerBaseSettings:
        """Apply base-trigger settings (SCPI values) and return the values read back."""
        if not self.is_connected():
            raise RuntimeError("Cannot set trigger base: not connected to instrument")

        root = scpi.ROOT_TRIGGER
        self._instrument.setSource(root, settings.source)
        self._instrument.setCount(root, settings.count)
        self._instrument.setEcount(root, settings.ecount)
        # Value before the AUTO state, so the AUTO state is the one left set
        # (on the instrument writing the value does not change AUTO, the order is a safeguard)
        self._instrument.setDelay(root, settings.delay)
        self._instrument.setDelayMode(root, settings.delay_auto)
        self._instrument.setHoldoff(root, settings.holdoff)
        self._instrument.setHoldoffAuto(root, settings.holdoff_auto)
        if settings.source == scpi.TRIGGER_SOURCE_TIMER:
            self._instrument.setTimer(root, settings.timer)
        if settings.source == scpi.TRIGGER_SOURCE_EXTERNAL:
            self._instrument.setExternal(root, settings.ext_edge)
        if settings.source == scpi.TRIGGER_SOURCE_INTERNAL:
            self._instrument.setCoupling(root, settings.sig_coupling)
            self._instrument.setSlope(root, settings.sig_slope)
            self._instrument.setLevel(root, settings.sig_level)
            self._instrument.setFilter(root, settings.sig_filter)
        self._instrument.check_errors()

        # Read back only after all writes; timer, edge and signal were sent
        # only for their source, the others keep the requested values
        layer = self._get_trigger_layer(root, settings)
        actual = replace(
            settings,
            source=layer.source,
            count=layer.count,
            ecount=layer.ecount,
            delay=layer.delay,
            delay_auto=layer.delay_auto,
            holdoff=layer.holdoff,
            holdoff_auto=layer.holdoff_auto,
            timer=layer.timer,
        )
        if settings.source == scpi.TRIGGER_SOURCE_EXTERNAL:
            actual = replace(actual, ext_edge=self._instrument.get_trigger_external(root))
        if settings.source == scpi.TRIGGER_SOURCE_INTERNAL:
            signal = self._instrument.get_trigger_signal(root)
            actual = replace(
                actual,
                sig_coupling=signal["coupling"],
                sig_slope=signal["slope"],
                sig_level=signal["level"],
                sig_filter=signal["filter"],
            )
        return actual

    def set_trigger_advanced(self, settings: TriggerAdvancedSettings) -> TriggerAdvancedSettings:
        """Apply advanced-trigger settings (SCPI values) and return the values read back."""
        if not self.is_connected():
            raise RuntimeError("Cannot set trigger advanced: not connected to instrument")

        for root, layer in (
            (scpi.ROOT_ARM2, settings.arm2),
            (scpi.ROOT_ARM1, settings.arm1),
            (scpi.ROOT_TRIGGER, settings.trigger),
        ):
            self._set_trigger_layer(root, layer, settings.ext_edge, settings.signal)

        # Initiate last: CONT ON starts the trigger cycle with the layers already set
        root = scpi.ROOT_INITIATE
        if settings.initiate_mode == scpi.INITIATE_EPOCH:
            # Epoch switches CONT to ON at start and back to OFF at stop
            self._instrument.setContinuos(root, False)
            self._instrument.setEpochStart(root, settings.epoch_start)
            self._instrument.setEpochStop(root, settings.epoch_stop)
        else:
            # A previous Epoch would still switch CONT at its dates
            self._instrument.setEpochStart(root, scpi.EPOCH_DISABLED)
            self._instrument.setEpochStop(root, scpi.EPOCH_DISABLED)
            self._instrument.setContinuos(
                root, settings.initiate_mode == scpi.INITIATE_CONTINUOUS_ON
            )
        self._instrument.check_errors()

        # Read back only after all writes
        return self._read_trigger_advanced(settings)

    def get_trigger_advanced(self, fallback: TriggerAdvancedSettings) -> TriggerAdvancedSettings:
        """
        Read back the whole trigger state without writing anything (SCPI values):
        timer, edge and signal too, whatever the sources. Initiate mode and
        Epoch dates cannot be read back and keep the fallback values.
        """
        if not self.is_connected():
            raise RuntimeError("Cannot get trigger advanced: not connected to instrument")

        return self._read_trigger_advanced(fallback, complete=True)

    def _read_trigger_advanced(
        self, fallback: TriggerAdvancedSettings, complete: bool = False
    ) -> TriggerAdvancedSettings:
        """
        Read back the event layers. Initiate mode and Epoch dates keep the
        fallback values: CONT? cannot tell Epoch from Continuous OFF. Unless
        complete, timer, edge and signal are read only for the sources that
        use them, as they are sent only then.
        """
        layers = {
            "arm2": (scpi.ROOT_ARM2, fallback.arm2),
            "arm1": (scpi.ROOT_ARM1, fallback.arm1),
            "trigger": (scpi.ROOT_TRIGGER, fallback.trigger),
        }
        actual = replace(fallback, **{
            name: self._get_trigger_layer(root, None if complete else layer)
            for name, (root, layer) in layers.items()
        })
        roots = [root for root, _ in layers.values()]
        sources = [actual.arm2.source, actual.arm1.source, actual.trigger.source]
        # Edge and signal are common to all layers (:TRIG:RESet resets them too):
        # read them from any layer, or from the first one using them
        external = complete or scpi.TRIGGER_SOURCE_EXTERNAL in sources
        signal_root = scpi.ROOT_TRIGGER if complete else next(
            (root for root, source in zip(roots, sources) if source == scpi.TRIGGER_SOURCE_INTERNAL),
            None,
        )
        if external:
            actual = replace(
                actual, ext_edge=self._instrument.get_trigger_external(scpi.ROOT_TRIGGER)
            )
        if signal_root is not None:
            actual = replace(
                actual, signal=TriggerSignalSettings(**self._instrument.get_trigger_signal(signal_root))
            )
        return actual

    def _get_trigger_layer(self, root: str, requested):
        """
        Read back one event layer; the timer only when the source is Timer,
        as it is sent only then. requested is a layer or base-trigger settings,
        None to keep the timer read from the instrument whatever the source.
        """
        holdoff = root == scpi.ROOT_TRIGGER
        layer = self._instrument.get_trigger_layer(root, holdoff=holdoff)
        if requested is not None and layer["source"] != scpi.TRIGGER_SOURCE_TIMER:
            layer["timer"] = requested.timer
        if holdoff:
            return TriggerLayerHoldoffSettings(**layer)
        return TriggerLayerSettings(**layer)

    def _set_trigger_layer(
        self,
        root: str,
        layer: TriggerLayerSettings,
        ext_edge: str,
        signal: TriggerSignalSettings,
    ) -> None:
        """Apply one event layer; ext_edge and signal are sent only if its source uses them."""
        self._instrument.setSource(root, layer.source)
        self._instrument.setCount(root, layer.count)
        self._instrument.setEcount(root, layer.ecount)
        # Value before the AUTO state, so the AUTO state is the one left set
        self._instrument.setDelay(root, layer.delay)
        self._instrument.setDelayMode(root, layer.delay_auto)
        if isinstance(layer, TriggerLayerHoldoffSettings):
            self._instrument.setHoldoff(root, layer.holdoff)
            self._instrument.setHoldoffAuto(root, layer.holdoff_auto)
        if layer.source == scpi.TRIGGER_SOURCE_TIMER:
            self._instrument.setTimer(root, layer.timer)
        if layer.source == scpi.TRIGGER_SOURCE_EXTERNAL:
            self._instrument.setExternal(root, ext_edge)
        if layer.source == scpi.TRIGGER_SOURCE_INTERNAL:
            self._instrument.setCoupling(root, signal.coupling)
            self._instrument.setSlope(root, signal.slope)
            self._instrument.setLevel(root, signal.level)
            self._instrument.setFilter(root, signal.filter)
    
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