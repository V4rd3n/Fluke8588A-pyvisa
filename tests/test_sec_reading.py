import pyvisa


def main() -> None:
    """Read primary, secondary, and timestamp data from Fluke 8588A."""
    resource_name = "USB0::3966::32777::651684161::0::INSTR"
    resource_manager = pyvisa.ResourceManager("@py")
    instrument = None
    try:
        instrument = resource_manager.open_resource(resource_name)
        instrument.timeout = 5000
        
        # Reset stato ed errori
        instrument.write("*CLS")
        
        print(f"Instrument: {instrument.query('*IDN?').strip()}")
        
        # 1. Abilitazione corretta del Timer dei Timestamp sul Fluke 8588A
        instrument.write(":SYST:TIME:TIMer ON")
        
        # Verify timer status
        timer_state = instrument.query(":SYST:TIME:TIMer:STAT?").strip()
        print(f"Timestamp timer state: {timer_state}")
        # Avvia la misurazione
        instrument.write(":INITiate:IMMediate")

        for measurement_number in range(1, 11):
            print(f"\n{'=' * 60}\nMeasurement {measurement_number}\n{'=' * 60}")

            # Sincronizzazione dell'esecuzione completata
            instrument.query("*OPC?")
            
            # Read primary reading (RMS Voltage/Current)
            val_primary = instrument.query(":FETCh? 1").strip()
            
            # Read secondary reading (Frequency/Period/etc.)
            val_secondary = instrument.query(":FETCh? 2").strip()
            
            # Read current relative timestamp timer value
            val_timestamp = instrument.query(":FETCh? 5").strip()
            
            print(f"Primary (Index 1)  : {val_primary}")
            print(f"Secondary (Index 2): {val_secondary}")
            print(f"Time Offset (s)    : {val_timestamp}")
                
    finally:
        if instrument is not None:
            instrument.close()
        resource_manager.close()


if __name__ == "__main__":
    main()