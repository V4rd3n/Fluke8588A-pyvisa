from pathlib import Path
from PyQt6 import QtWidgets, uic
import sys

ROOT = Path(__file__).resolve().parents[1]
UI_FILE = ROOT / "new_ui" / "trigger_base.ui"


def read_trigger_settings(window):
	settings = {
		"event": window.comboBox.currentText(),
		"delay_mode": "AUTO" if window.radioButton_2.isChecked() else "MANUAL",
		"delay": window.doubleSpinBox.value(),
		"holdoff_mode": "AUTO" if window.radioButton_3.isChecked() else "MANUAL",
		"holdoff": window.doubleSpinBox_2.value(),
		"count": window.spinBox.value(),
		"ecount": window.spinBox_2.value(),
	}
	if window.comboBox.currentText() == "Timer":
		settings["timer_ns"] = window.spinBox_3.value()
	if window.comboBox.currentText() == "External":
		settings["external_edge"] = window.comboBox_2.currentText()
	return settings


def print_trigger_settings(window):
	print(read_trigger_settings(window))


def set_delay_mode(enabled):
	window.doubleSpinBox.setEnabled(enabled)


def set_holdoff_mode(enabled):
	window.doubleSpinBox_2.setEnabled(enabled)


def set_row_visible(row, visible):
	for index in range(row.count()):
		item = row.itemAt(index)
		if item.widget() is not None:
			item.widget().setVisible(visible)


def update_event_rows(event):
	set_row_visible(window.timer_row, event == "Timer")
	set_row_visible(window.external_row, event == "External")


app = QtWidgets.QApplication(sys.argv)
window = uic.loadUi(str(UI_FILE))

window.comboBox.setCurrentText("Immediate")
window.doubleSpinBox.setRange(0.0, 999999.0)
window.doubleSpinBox_2.setRange(0.00000003, 4000000.0)
window.doubleSpinBox.setValue(1.0)
window.doubleSpinBox_2.setValue(1.0)
window.spinBox.setRange(1, 1000000)
window.spinBox_2.setRange(1, 1000000)
window.spinBox_3.setRange(0, 999999999)

window.radioButton.toggled.connect(set_delay_mode)
window.radioButton_4.toggled.connect(set_holdoff_mode)
window.comboBox.currentTextChanged.connect(update_event_rows)

for widget in (
	window.comboBox,
	window.radioButton,
	window.radioButton_2,
	window.radioButton_3,
	window.radioButton_4,
	window.doubleSpinBox,
	window.doubleSpinBox_2,
	window.spinBox,
	window.spinBox_2,
):
	if hasattr(widget, "currentTextChanged"):
		widget.currentTextChanged.connect(lambda *_: print_trigger_settings(window))
	elif hasattr(widget, "toggled"):
		widget.toggled.connect(lambda *_: print_trigger_settings(window))
	else:
		widget.valueChanged.connect(lambda *_: print_trigger_settings(window))

set_delay_mode(window.radioButton.isChecked())
set_holdoff_mode(window.radioButton_4.isChecked())
update_event_rows(window.comboBox.currentText())
print_trigger_settings(window)
window.show()

app.exec()