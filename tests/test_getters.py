import logging
from src.Fluke8588A.Fluke8588A import Fluke8588A
from src.Fluke8588A.config import InstrumentConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def test_getters():
    """
    Test all getter functions to see their output types and values.
    """
    try:
        # Connect and initialize
        fluke = Fluke8588A(InstrumentConfig.DEFAULT_ADDRESS)
        print(f"Connected: {fluke.identify()}\n")
        
        # Initialize resistance mode
        root = InstrumentConfig.ROOT_RESISTANCE
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
        
        print("=== GETTER FUNCTION OUTPUTS (RESISTANCE MODE) ===\n")
        
        # Test getters relevant to resistance mode
        print("--- Basic Settings ---")
        
        result = fluke.getApertureMode(root)
        print(f"getApertureMode output: {repr(result)}, type: {type(result).__name__}")
        
        result = fluke.getTime(root)
        print(f"getTime output: {repr(result)}, type: {type(result).__name__}")
        
        result = fluke.getRange(root)
        print(f"getRange output: {repr(result)}, type: {type(result).__name__}")
        
        result = fluke.getRangeMode(root)
        print(f"getRangeMode output: {repr(result)}, type: {type(result).__name__}")
        
        result = fluke.getResolution(root)
        print(f"getResolution output: {repr(result)}, type: {type(result).__name__}")
        
        result = fluke.getFilter(root)
        print(f"getFilter output: {repr(result)}, type: {type(result).__name__}")
        
        # Test wire mode getter if it exists
        try:
            result = fluke.getWireMode(root)
            print(f"getWireMode output: {repr(result)}, type: {type(result).__name__}")
        except AttributeError:
            print("getWireMode: NOT AVAILABLE")
        
        # Test low current mode getter if it exists
        try:
            result = fluke.getLowCurrentMode(root)
            print(f"getLowCurrentMode output: {repr(result)}, type: {type(result).__name__}")
        except AttributeError:
            print("getLowCurrentMode: NOT AVAILABLE")
        
        fluke.close()
        print("\n" + "="*50 + "\n")
        
        # Test DCV mode
        print("=== DCV MODE GETTERS ===\n")
        fluke = Fluke8588A(InstrumentConfig.DEFAULT_ADDRESS)
        root_dcv = InstrumentConfig.ROOT_DCV
        
        fluke.init_dcv(
            range_mode="AUTO",
            range_val="AUTO",
            resolution_val=4,
            zin="AUTO",
            aperture_mode="AUTO",
            time_val=1
        )
        
        print("--- DCV Specific Settings ---")
        
        result = fluke.getApertureMode(root_dcv)
        print(f"getApertureMode output: {repr(result)}, type: {type(result).__name__}")
        
        result = fluke.getTime(root_dcv)
        print(f"getTime output: {repr(result)}, type: {type(result).__name__}")
        
        result = fluke.getRange(root_dcv)
        print(f"getRange output: {repr(result)}, type: {type(result).__name__}")
        
        result = fluke.getRangeMode(root_dcv)
        print(f"getRangeMode output: {repr(result)}, type: {type(result).__name__}")
        
        result = fluke.getResolution(root_dcv)
        print(f"getResolution output: {repr(result)}, type: {type(result).__name__}")
        
        result = fluke.getImp(root_dcv)
        print(f"getImp output: {repr(result)}, type: {type(result).__name__}")
        
        fluke.close()
        print("\n" + "="*50 + "\n")
        
        # Test DCI mode
        print("=== DCI MODE GETTERS ===\n")
        fluke = Fluke8588A(InstrumentConfig.DEFAULT_ADDRESS)
        root_dci = InstrumentConfig.ROOT_DCI
        
        fluke.init_dci(
            range_mode="AUTO",
            range_val="AUTO",
            resolution_val=4,
            aperture_mode="AUTO",
            time_val=1
        )
        
        print("--- DCI Specific Settings ---")
        
        result = fluke.getApertureMode(root_dci)
        print(f"getApertureMode output: {repr(result)}, type: {type(result).__name__}")
        
        result = fluke.getTime(root_dci)
        print(f"getTime output: {repr(result)}, type: {type(result).__name__}")
        
        result = fluke.getRange(root_dci)
        print(f"getRange output: {repr(result)}, type: {type(result).__name__}")
        
        result = fluke.getRangeMode(root_dci)
        print(f"getRangeMode output: {repr(result)}, type: {type(result).__name__}")
        
        result = fluke.getResolution(root_dci)
        print(f"getResolution output: {repr(result)}, type: {type(result).__name__}")
        
        # Test counter-related getters for DCI
        try:
            result = fluke.getBlimit(root_dci)
            print(f"getBlimit output: {repr(result)}, type: {type(result).__name__}")
        except Exception as e:
            print(f"getBlimit: ERROR - {e}")
        
        try:
            result = fluke.getCounterCoupling(root_dci)
            print(f"getCounterCoupling output: {repr(result)}, type: {type(result).__name__}")
        except Exception as e:
            print(f"getCounterCoupling: ERROR - {e}")
        
        try:
            result = fluke.getCounterGate(root_dci)
            print(f"getCounterGate output: {repr(result)}, type: {type(result).__name__}")
        except Exception as e:
            print(f"getCounterGate: ERROR - {e}")
        
        fluke.close()
        print("\n" + "="*50)
        
    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    test_getters()
