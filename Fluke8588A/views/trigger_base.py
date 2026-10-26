from PyQt6 import uic
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import pyqtSignal
import os
from Fluke8588A.data import gui_values
from Fluke8588A.data.settings import TriggerBaseSettings

#TODO: fix auto on/off not working, fix external edge selection, add ranges 



trigger_base_window_loc = os.path.join(
    os.path.dirname(__file__), "..", "ui", "trigger_base.ui"
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
        self.delautoon_radio.toggled.connect(self._update_auto_controls)
        self.holdautoon_radio.toggled.connect(self._update_auto_controls)

    def _init_widgets(self):
        self.tevent_combobox.clear()
        self.tevent_combobox.addItems(gui_values.TRIGGER_SOURCES)
        self.ext_combobox.clear()
        self.ext_combobox.addItems(gui_values.TRIGGER_EXTERNAL_EDGES)
        self.tcount_spinbox.setRange(*gui_values.TRIGGER_COUNT_RANGE)
        self.tecount_spinbox.setRange(*gui_values.TRIGGER_ECOUNT_RANGE)
        # Decimals before the ranges, setRange rounds to the current decimals
        self.del_doublespinbox.setDecimals(gui_values.TRIGGER_DELAY_DECIMALS)
        self.hold_doublespinbox.setDecimals(gui_values.TRIGGER_HOLDOFF_DECIMALS)
        self.tim_doublespinbox.setDecimals(gui_values.TRIGGER_TIMER_DECIMALS)
        self.del_doublespinbox.setRange(*gui_values.TRIGGER_DELAY_RANGE)
        self.hold_doublespinbox.setRange(*gui_values.TRIGGER_HOLDOFF_RANGE)
        self.tim_doublespinbox.setRange(*gui_values.TRIGGER_TIMER_RANGE)
        self.tlevel_spinbox.setRange(*gui_values.TRIGGER_LEVEL_RANGE)
        self._set_source_defaults()
        self._update_source_widgets(self.tevent_combobox.currentText())
        self._update_auto_controls()

    def _update_source_widgets(self, source: str) -> None:
        self._set_source_defaults()
        timer_visible = (source == gui_values.TRIGGER_SOURCE_TIMER)
        self.label_6.setVisible(timer_visible)
        self.tim_doublespinbox.setVisible(timer_visible)

        external_visible = (source == gui_values.TRIGGER_SOURCE_EXTERNAL)
        self.label_8.setVisible(external_visible)
        self.ext_combobox.setVisible(external_visible)

        self.signal_groupbox.setVisible(source == gui_values.TRIGGER_SOURCE_INTERNAL)
        self._update_auto_controls()

    def _update_auto_controls(self) -> None:
        self.del_doublespinbox.setEnabled(not self.delautoon_radio.isChecked())
        self.hold_doublespinbox.setEnabled(not self.holdautoon_radio.isChecked())

    def _set_source_defaults(self) -> None:
        source = self.tevent_combobox.currentText()
        if source == gui_values.TRIGGER_SOURCE_TIMER:
            self.tim_doublespinbox.setValue(0.0)
        elif source == gui_values.TRIGGER_SOURCE_EXTERNAL:
            self.ext_combobox.setCurrentIndex(0)
        elif source == gui_values.TRIGGER_SOURCE_INTERNAL:
            self.tdccoup_radiobutton.setChecked(True)
            self.tpos_radiobutton.setChecked(True)
            self.tlevel_spinbox.setValue(0)
            self.tfiltoff_radiobutton.setChecked(True)

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
        self._update_auto_controls()
        self.tim_doublespinbox.setValue(settings.timer if settings.timer is not None else 0.0)
        self._set_external_edge(settings.ext_edge)
        self.tdccoup_radiobutton.setChecked(False)
        self.taccoup_radiobutton.setChecked(False)
        if source == gui_values.TRIGGER_SOURCE_INTERNAL and settings.sig_coupling == gui_values.TRIGGER_COUPLING_DC:
            self.tdccoup_radiobutton.setChecked(True)
        elif source == gui_values.TRIGGER_SOURCE_INTERNAL and settings.sig_coupling == gui_values.TRIGGER_COUPLING_AC:
            self.taccoup_radiobutton.setChecked(True)
        self.tpos_radiobutton.setChecked(False)
        self.tneg_radiobutton.setChecked(False)
        if source == gui_values.TRIGGER_SOURCE_INTERNAL and settings.sig_slope in ("+", gui_values.TRIGGER_SLOPE_POS):
            self.tpos_radiobutton.setChecked(True)
        elif source == gui_values.TRIGGER_SOURCE_INTERNAL and settings.sig_slope in ("-", gui_values.TRIGGER_SLOPE_NEG):
            self.tneg_radiobutton.setChecked(True)
        self.tlevel_spinbox.setValue(
            int(settings.sig_level) if source == gui_values.TRIGGER_SOURCE_INTERNAL and settings.sig_level is not None else 0
        )
        self.tfilton_radiobutton.setChecked(
            source == gui_values.TRIGGER_SOURCE_INTERNAL and settings.sig_filter is True
        )
        self.tfiltoff_radiobutton.setChecked(
            source == gui_values.TRIGGER_SOURCE_INTERNAL and settings.sig_filter is False
        )

    def get_settings(self) -> TriggerBaseSettings:
        sig_coupling = (
            gui_values.TRIGGER_COUPLING_DC if self.tdccoup_radiobutton.isChecked()
            else gui_values.TRIGGER_COUPLING_AC if self.taccoup_radiobutton.isChecked()
            else None
        )
        sig_slope = (
            gui_values.TRIGGER_SLOPE_POS if self.tpos_radiobutton.isChecked()
            else gui_values.TRIGGER_SLOPE_NEG if self.tneg_radiobutton.isChecked()
            else None
        )
        signal_configured = self.tevent_combobox.currentText() == gui_values.TRIGGER_SOURCE_INTERNAL
        external_edge = self.ext_combobox.currentText()
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
                if self.tevent_combobox.currentText() == gui_values.TRIGGER_SOURCE_TIMER
                else 0.0
            ),
            ext_edge=(
                external_edge
                if self.tevent_combobox.currentText() == gui_values.TRIGGER_SOURCE_EXTERNAL
                else gui_values.TRIGGER_EXTERNAL_EDGES[0]
            ),
            sig_coupling=(sig_coupling or gui_values.TRIGGER_COUPLING_DC) if signal_configured else gui_values.TRIGGER_COUPLING_DC,
            sig_slope=(sig_slope or gui_values.TRIGGER_SLOPE_POS) if signal_configured else gui_values.TRIGGER_SLOPE_POS,
            sig_level=self.tlevel_spinbox.value() if signal_configured else 0,
            sig_filter=(
                self.tfilton_radiobutton.isChecked()
                if signal_configured and (
                    self.tfilton_radiobutton.isChecked()
                    or self.tfiltoff_radiobutton.isChecked()
                )
                else False
            ),
        )

    def _set_external_edge(self, edge: str | None) -> None:
        self.ext_combobox.setCurrentIndex(0)
        if edge in gui_values.TRIGGER_EXTERNAL_EDGES:
            self.ext_combobox.setCurrentText(edge)
