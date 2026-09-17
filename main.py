from PyQt6.QtWidgets import QApplication
from src.Fluke8588A.app_controller import AppController
import sys
import importlib.util
from pathlib import Path


def import_local_package(package_name: str, relative_path: str):
    pkg_path = Path(__file__).resolve().parent / relative_path / "__init__.py"

    spec = importlib.util.spec_from_file_location(package_name, pkg_path)
    if spec is None or spec.loader is None:
        raise ImportError(
            f"Impossibile trovare il pacchetto {package_name} in {pkg_path}"
        )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

mio_strumento = import_local_package("mio_strumento", "src/mio_strumento")

def main():
    app = QApplication(sys.argv)
    app_controller = AppController()
    app.exec()


if __name__ == "__main__":
    main()