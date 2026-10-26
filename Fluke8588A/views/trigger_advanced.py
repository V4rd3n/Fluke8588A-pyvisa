from dataclasses import dataclass
from PyQt6 import uic
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QRadioButton,
    QSpinBox,
    QWidget,
)
from PyQt6.QtCore import QDateTime, pyqtSignal
import os
from Fluke8588A.data import gui_values
from Fluke8588A.data.settings import (
    TriggerAdvancedSettings,
    TriggerLayerHoldoffSettings,
    TriggerLayerSettings,
    TriggerSignalSettings,
)


trigger_advanced_window_loc = os.path.join(
    os.path.dirname(__file__), "..", "ui", "trigger_advanced.ui"
)


@dataclass
class _LayerWidgets:
    """Widgets of one event layer tab (ARM2, ARM1, Trigger)."""
    source:         QComboBox
    count:          QSpinBox
    ecount:         QSpinBox
    delay:          QDoubleSpinBox
    delay_auto_on:  QRadioButton
    delay_auto_off: QRadioButton
    timer:          QDoubleSpinBox
    timer_label:    QLabel


class TriggerAdvancedWindow(QWidget):
    set_requested = pyqtSignal()
    reset_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        uic.loadUi(trigger_advanced_window_loc, self)
        self.setWindowTitle("Advanced Trigger Settings")
        # The .ui widget names do not follow the tabs: map them here once
        self._arm2 = _LayerWidgets(
            source=self.tevent_combobox,
            count=self.tcount_spinbox,
            ecount=self.tecount_spinbox,
            delay=self.del_doublespinbox,
            delay_auto_on=self.delautoon_radio,
            delay_auto_off=self.delautooff_radio,
            timer=self.tim_doublespinbox_3,
            timer_label=self.label_24,
        )
        self._arm1 = _LayerWidgets(
            source=self.tevent_combobox_3,
            count=self.tcount_spinbox_3,
            ecount=self.tecount_spinbox_3,
            delay=self.del_doublespinbox_3,
            delay_auto_on=self.delautoon_radio_3,
            delay_auto_off=self.delautooff_radio_3,
            timer=self.tim_doublespinbox_2,
            timer_label=self.label_23,
        )
        self._trigger = _LayerWidgets(
            source=self.tevent_combobox_2,
            count=self.tcount_spinbox_2,
            ecount=self.tecount_spinbox_2,
            delay=self.del_doublespinbox_2,
            delay_auto_on=self.delautoon_radio_2,
            delay_auto_off=self.delautooff_radio_2,
            timer=self.tim_doublespinbox,
            timer_label=self.label_22,
        )
        self._layers = (self._arm2, self._arm1, self._trigger)
        self._connect_signals()
        self._init_widgets()

    def _connect_signals(self):
        self.taset_pushbutton.pressed.connect(self.set_requested)
        self.tareset_pushbutton_2.pressed.connect(self.reset_requested)
        self.comboBox.currentTextChanged.connect(self._update_epoch_controls)
        for layer in self._layers:
            layer.source.currentTextChanged.connect(self._update_source_widgets)
            layer.delay_auto_on.toggled.connect(self._update_auto_controls)
        self.holdautoon_radio_2.toggled.connect(self._update_auto_controls)

    def _init_widgets(self):
        self.comboBox.clear()
        self.comboBox.addItems(gui_values.TRIGGER_INITIATE_MODES)
        for datetime_edit in (self.startepoch_datetime, self.stopepoch_datetime):
            datetime_edit.setDisplayFormat(gui_values.TRIGGER_EPOCH_DISPLAY_FORMAT)
            datetime_edit.setCalendarPopup(True)
        self.ext_combobox.clear()
        self.ext_combobox.addItems(gui_values.TRIGGER_EXTERNAL_EDGES)
        self.tlevel_spinbox.setRange(*gui_values.TRIGGER_LEVEL_RANGE)
        for layer in self._layers:
            layer.source.clear()
            layer.source.addItems(gui_values.TRIGGER_SOURCES)
            layer.count.setRange(*gui_values.TRIGGER_COUNT_RANGE)
            layer.ecount.setRange(*gui_values.TRIGGER_ECOUNT_RANGE)
            # Decimals before the ranges, setRange rounds to the current decimals
            layer.delay.setDecimals(gui_values.TRIGGER_DELAY_DECIMALS)
            layer.timer.setDecimals(gui_values.TRIGGER_TIMER_DECIMALS)
            layer.delay.setRange(*gui_values.TRIGGER_DELAY_RANGE)
            layer.timer.setRange(*gui_values.TRIGGER_TIMER_RANGE)
        self.hold_doublespinbox_2.setDecimals(gui_values.TRIGGER_HOLDOFF_DECIMALS)
        self.hold_doublespinbox_2.setRange(*gui_values.TRIGGER_HOLDOFF_RANGE)
        self._update_epoch_controls()
        self._update_source_widgets()
        self._update_auto_controls()

    def _update_epoch_controls(self, *_) -> None:
        epoch = self.comboBox.currentText() == gui_values.TRIGGER_INITIATE_EPOCH
        self.startepoch_datetime.setEnabled(epoch)
        self.stopepoch_datetime.setEnabled(epoch)

    def _update_source_widgets(self, *_) -> None:
        for layer in self._layers:
            timer_visible = layer.source.currentText() == gui_values.TRIGGER_SOURCE_TIMER
            layer.timer_label.setVisible(timer_visible)
            layer.timer.setVisible(timer_visible)
        # Edge and signal are shared by the layers: editable if any layer uses them
        sources = [layer.source.currentText() for layer in self._layers]
        self.exttype_groupbox.setEnabled(gui_values.TRIGGER_SOURCE_EXTERNAL in sources)
        self.signal_groupbox.setEnabled(gui_values.TRIGGER_SOURCE_INTERNAL in sources)

    def _update_auto_controls(self, *_) -> None:
        for layer in self._layers:
            layer.delay.setEnabled(not layer.delay_auto_on.isChecked())
        self.hold_doublespinbox_2.setEnabled(not self.holdautoon_radio_2.isChecked())

    def set_settings(self, settings: TriggerAdvancedSettings) -> None:
        self.comboBox.setCurrentText(settings.initiate_mode)
        self.startepoch_datetime.setDateTime(QDateTime(settings.epoch_start))
        self.stopepoch_datetime.setDateTime(QDateTime(settings.epoch_stop))
        self.ext_combobox.setCurrentIndex(0)
        if settings.ext_edge in gui_values.TRIGGER_EXTERNAL_EDGES:
            self.ext_combobox.setCurrentText(settings.ext_edge)
        self._set_signal(settings.signal)
        self._set_layer(self._arm2, settings.arm2)
        self._set_layer(self._arm1, settings.arm1)
        self._set_layer(self._trigger, settings.trigger)
        self.hold_doublespinbox_2.setValue(settings.trigger.holdoff)
        self.holdautoon_radio_2.setChecked(settings.trigger.holdoff_auto)
        self.holdautooff_radio_2.setChecked(not settings.trigger.holdoff_auto)
        self._update_epoch_controls()
        self._update_source_widgets()
        self._update_auto_controls()

    def _set_signal(self, signal: TriggerSignalSettings) -> None:
        if signal.coupling == gui_values.TRIGGER_COUPLING_AC:
            self.taccoup_radiobutton.setChecked(True)
        else:
            self.tdccoup_radiobutton.setChecked(True)
        if signal.slope == gui_values.TRIGGER_SLOPE_NEG:
            self.tneg_radiobutton.setChecked(True)
        else:
            self.tpos_radiobutton.setChecked(True)
        self.tlevel_spinbox.setValue(signal.level)
        if signal.filter:
            self.tfilton_radiobutton.setChecked(True)
        else:
            self.tfiltoff_radiobutton.setChecked(True)

    def _set_layer(self, widgets: _LayerWidgets, layer: TriggerLayerSettings) -> None:
        widgets.source.setCurrentText(layer.source)
        widgets.count.setValue(layer.count)
        widgets.ecount.setValue(layer.ecount)
        widgets.delay.setValue(layer.delay)
        widgets.delay_auto_on.setChecked(layer.delay_auto)
        widgets.delay_auto_off.setChecked(not layer.delay_auto)
        widgets.timer.setValue(layer.timer)

    def get_settings(self) -> TriggerAdvancedSettings:
        arm2 = self._get_layer(self._arm2)
        arm1 = self._get_layer(self._arm1)
        trigger = self._get_layer(self._trigger)
        return TriggerAdvancedSettings(
            initiate_mode=self.comboBox.currentText(),
            epoch_start=self.startepoch_datetime.dateTime().toPyDateTime(),
            epoch_stop=self.stopepoch_datetime.dateTime().toPyDateTime(),
            ext_edge=self.ext_combobox.currentText(),
            signal=TriggerSignalSettings(
                coupling=(
                    gui_values.TRIGGER_COUPLING_AC if self.taccoup_radiobutton.isChecked()
                    else gui_values.TRIGGER_COUPLING_DC
                ),
                slope=(
                    gui_values.TRIGGER_SLOPE_NEG if self.tneg_radiobutton.isChecked()
                    else gui_values.TRIGGER_SLOPE_POS
                ),
                level=self.tlevel_spinbox.value(),
                filter=self.tfilton_radiobutton.isChecked(),
            ),
            arm2=arm2,
            arm1=arm1,
            trigger=TriggerLayerHoldoffSettings(
                **vars(trigger),
                holdoff=self.hold_doublespinbox_2.value(),
                holdoff_auto=self.holdautoon_radio_2.isChecked(),
            ),
        )

    def _get_layer(self, widgets: _LayerWidgets) -> TriggerLayerSettings:
        return TriggerLayerSettings(
            source=widgets.source.currentText(),
            count=widgets.count.value(),
            ecount=widgets.ecount.value(),
            delay=widgets.delay.value(),
            delay_auto=widgets.delay_auto_on.isChecked(),
            timer=widgets.timer.value(),
        )
