import pyqtgraph as pg
import random
from PyQt6 import QtCore
class DmmPlotWidget(pg.PlotWidget):

	def __init__(self, parent=None):
		super().__init__(parent)
		self.seconds=0.00
		self.data =[]
		self.time=[]
		self.parent=parent
	
	def _creatUpdateTimer(self):
		t = QtCore.QTimer()
		t.timeout.connect(self.updatePlot)
		t.start(50)

	def _connect_signals(self, main_window=None):
		if main_window and hasattr(main_window, 'append_value'):
			main_window.append_value.connect(self.addValue)
	
	def drawTest(self):
		# Plot initial empty data
		self.plot(self.time, self.data)
		

	def addValue(self, value:int):
		self.seconds+=0.1 #to be changed, by using import time
		self.time.append(self.seconds)
		self.data.append(value)
		self.plotData()
	
	def updatePlot(self):
		self.plot(self.time, self.data, clear=True)

	def plotData(self):
		self.plot(self.time, self.data)
