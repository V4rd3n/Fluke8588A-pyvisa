from dataclasses import dataclass
from PyQt6.QtCore import Qt
from Fluke8588A.views.reading_panel import LEFT_AXIS_WIDTH, POINT_SIZE
import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters

# Enough to see the shape of the data, the values are in the CSV file
PNG_SIZE = (800, 600)


@dataclass
class PlotData:
    """
    One plot of a PNG: x and y data (nan for the points left out), labels and
    units of the axes. With units the axis picks its SI prefix, None when the
    unit is already in the label (dB).
    """
    x: object
    y: object
    x_label: str
    x_units: str | None
    y_label: str
    y_units: str | None
    # A marker on each point, as the graph window
    symbols: bool = False


def export_png(path, plots: list[PlotData], size: tuple[int, int] = PNG_SIZE) -> None:
    """
    PNG of plots stacked one below the other, drawn off screen at size: the
    same image whatever the size of the window, also when it is hidden.
    """
    width, height = size
    widget = pg.GraphicsLayoutWidget()
    # Shown so that the layout takes the size, but never on screen
    widget.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen)
    widget.resize(width, height)
    try:
        for row, data in enumerate(plots):
            plot = widget.addPlot(row=row, col=0)
            plot.showGrid(x=True, y=True)
            plot.setLabel("bottom", data.x_label, units=data.x_units)
            plot.setLabel("left", data.y_label, units=data.y_units)
            plot.getAxis("left").setWidth(LEFT_AXIS_WIDTH)
            # A digitize block can hold millions of samples, more than the pixels
            plot.setDownsampling(auto=True, mode="peak")
            plot.setClipToView(True)
            symbol = {"symbol": "o", "symbolSize": POINT_SIZE} if data.symbols else {}
            # A bin at exactly zero is -inf dB, the curve cannot draw it
            y = np.where(np.isfinite(data.y), data.y, np.nan) if len(data.y) else data.y
            plot.plot(data.x, y, connect="finite", **symbol)
        widget.show()
        exporter = pg.exporters.ImageExporter(widget.scene())
        # Both set, without the exporter keeping the aspect ratio of the scene
        exporter.parameters().param("width").setValue(width, blockSignal=exporter.widthChanged)
        exporter.parameters().param("height").setValue(height, blockSignal=exporter.heightChanged)
        exporter.export(str(path))
    finally:
        widget.close()
        widget.deleteLater()
