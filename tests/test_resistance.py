import logging
from src.Fluke8588A.instrument.Fluke8588A import Fluke8588A
from src.Fluke8588A.instrument.config import InstrumentConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def test_resistance():
    """
    Simple test for resistance measurement with Fluke 8588A.
    """
    try:
        # Connect and identify
        fluke = Fluke8588A(InstrumentConfig.DEFAULT_ADDRESS)
        print(f"Instrument: {fluke.identify()}")
        
        # Configure for resistance measurement (2-wire, AUTO range)
        fluke.init_resistance(
            aperture_mode="AUTO",
            time_val=1,
            mode_val="NORMal",
            low_mode_val=0,
            range_mode="AUTO",
            range_val="AUTO",
            resolution_val=4,
            filter_val=0
        )
        
        # Take measurement
        while input("enter to read")!="exit":
            reading = fluke.read()
            print(f"Resistance: {reading}")
        fluke.close()
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    test_resistance()
