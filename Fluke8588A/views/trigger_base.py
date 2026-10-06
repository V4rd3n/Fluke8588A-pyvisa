from PyQt6 import uic
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal
import os
from Fluke8588A.data.spin_box_values import (
    get_trigger_events
)
from Fluke8588A.data.settings import TriggerBaseSettings

#TODO: fix auto on/off not working, fix external edge selection, add ranges 



trigger_base_window_loc = os.path.join(
    os.path.dirname(__file__), "..", "new_ui", "trigger_base.ui"
)


class TriggerBaseWindow(QWidget):
    set_requested = pyqtSignal()
    reset_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        uic.loadUi(trigger_base_window_loc, self)
        self.setWindowTitle("Base Trigger Settings")
        self._connect_signals()
        self._init_widgets()

    def _connect_signals(self):
        self.tset_pushbutton.pressed.connect(self.set_requested)
        self.treset_pushbutton.pressed.connect(self.reset_requested)
        self.tevent_combobox.currentTextChanged.connect(self._update_source_widgets)

    def _init_widgets(self):
        self.tevent_combobox.clear()
        self.tevent_combobox.addItems(get_trigger_events())
        self.tcount_spinbox.setRange(1, 1_000_000)
        self.tecount_spinbox.setRange(1, 1_000_000)
        self.del_doublespinbox.setRange(0.0, 999_999.0)
        self.hold_doublespinbox.setRange(0.00000003, 4_000_000.0)
        self.tim_doublespinbox.setRange(0.0, 999_999_999.0)
        self.tlevel_spinbox.setRange(-1_000_000.0, 1_000_000.0)
        self._update_source_widgets(self.tevent_combobox.currentText())

    def _update_source_widgets(self, source: str) -> None:
        timer_visible = (source == "Timer")
        self.label_6.setVisible(timer_visible)
        self.tim_doublespinbox.setVisible(timer_visible)

        external_visible = (source == "External")
        self.label_8.setVisible(external_visible)
        self.ext_combobox.setVisible(external_visible)

        self.signal_groupbox.setVisible(source == "Internal")

    def set_settings(self, settings: TriggerBaseSettings) -> None:
        source = settings.source
        self.tevent_combobox.setCurrentText(source)
        self.tcount_spinbox.setValue(settings.count)
        self.tecount_spinbox.setValue(settings.ecount)
        self.del_doublespinbox.setValue(settings.delay)
        self.delautoon_radio.setChecked(settings.delay_auto)
        self.delautooff_radio.setChecked(not settings.delay_auto)
        self.hold_doublespinbox.setValue(settings.holdoff)
        self.holdautoon_radio.setChecked(settings.holdoff_auto)
        self.holdautooff_radio.setChecked(not settings.holdoff_auto)
        self.tim_doublespinbox.setValue(settings.timer or 0.0)
        self.ext_combobox.setCurrentIndex(0)
        if settings.ext_edge is not None:
            self.ext_combobox.setCurrentText(settings.ext_edge)
        self.tdccoup_radiobutton.setChecked(False)
        self.taccoup_radiobutton.setChecked(False)
        if source == "Internal" and settings.sig_coupling == "DC":
            self.tdccoup_radiobutton.setChecked(True)
        elif source == "Internal" and settings.sig_coupling == "AC":
            self.taccoup_radiobutton.setChecked(True)
        self.tpos_radiobutton.setChecked(False)
        self.tneg_radiobutton.setChecked(False)
        if source == "Internal" and settings.sig_slope in ("+", "POS"):
            self.tpos_radiobutton.setChecked(True)
        elif source == "Internal" and settings.sig_slope in ("-", "NEG"):
            self.tneg_radiobutton.setChecked(True)
        self.tlevel_spinbox.setValue(
            (settings.sig_level or 0.0) if source == "Internal" else 0.0
        )
        self.tfilton_radiobutton.setChecked(
            source == "Internal" and settings.sig_filter is True
        )
        self.tfiltoff_radiobutton.setChecked(
            source == "Internal" and settings.sig_filter is False
        )

    def get_settings(self) -> TriggerBaseSettings:
        sig_coupling = (
            "DC" if self.tdccoup_radiobutton.isChecked()
            else "AC" if self.taccoup_radiobutton.isChecked()
            else None
        )
        sig_slope = (
            "POS" if self.tpos_radiobutton.isChecked()
            else "NEG" if self.tneg_radiobutton.isChecked()
            else None
        )
        signal_configured = self.tevent_combobox.currentText() == "Internal"
        return TriggerBaseSettings(
            source=self.tevent_combobox.currentText(),
            count=self.tcount_spinbox.value(),
            ecount=self.tecount_spinbox.value(),
            delay=self.del_doublespinbox.value(),
            delay_auto=self.delautoon_radio.isChecked(),
            holdoff=self.hold_doublespinbox.value(),
            holdoff_auto=self.holdautoon_radio.isChecked(),
            timer=(
                self.tim_doublespinbox.value()
                if self.tevent_combobox.currentText() == "Timer"
                else None
            ),
            ext_edge=(
                self.ext_combobox.currentText()
                if self.tevent_combobox.currentText() == "External"
                else None
            ),
            sig_coupling=sig_coupling if signal_configured else None,
            sig_slope=sig_slope if signal_configured else None,
            sig_level=self.tlevel_spinbox.value() if signal_configured else None,
            sig_filter=(
                self.tfilton_radiobutton.isChecked()
                if signal_configured and (
                    self.tfilton_radiobutton.isChecked()
                    or self.tfiltoff_radiobutton.isChecked()
                )
                else None
            ),
        )