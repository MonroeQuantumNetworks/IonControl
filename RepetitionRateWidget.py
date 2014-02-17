import PyQt4.uic
from PyQt4 import QtGui, QtCore, QtSvg
import pyqtgraph
from pyqtgraph.dockarea import DockArea, Dock
from CoordinatePlotWidget import CoordinatePlotWidget
import pens
import Traceui


import logging

Form, Base = PyQt4.uic.loadUiType(r'ui\RepetitionRateWidget.ui')

class RepetitionRateWidget(Form, Base):
    def __init__(self,settings,pulserHardware,config,parent=None):
        Base.__init__(self,parent)
        Form.__init__(self)
        self.settings = settings
        self.pulser = pulserHardware
        self.config = config
        pyqtgraph.setConfigOption('background', 'w')
        pyqtgraph.setConfigOption('foreground', 'k')

    
    def setupUi(self):
        Form.setupUi(self,self)
        self.area = DockArea()
        self.setCentralWidget(self.area)
        # initialize all the plot windows we want
        self.plotWidgets = dict()   # Plot widgets in which stuff can be plotted
        self.mainDock = Dock("Errorsignal Trace")
        self.historyDock = Dock("History")
        self.area.addDock(self.mainDock,'left')
        self.area.addDock(self.historyDock,'right')
        self.graphicsWidget = CoordinatePlotWidget(self) # self.graphicsLayout.graphicsView
        self.mainDock.addWidget(self.graphicsWidget)
        self.graphicsView = self.graphicsWidget.graphicsView
        self.plotWidgets["Scan data"] =  self.graphicsView
        self.historyWidget = CoordinatePlotWidget(self)
        self.historyDock.addWidget(self.historyWidget)
        self.historyView = self.historyWidget.graphicsView
        self.historyWidget.autoRange()
        try:
            if self.experimentName+'.pyqtgraph-dockareastate' in self.config:
                self.area.restoreState(self.config[self.experimentName+'.pyqtgraph-dockareastate'])
        except:
            pass # Ignore errors on restoring the state. This might happen after a new dock is added
        self.penicons = pens.penicons().penicons()
        self.traceui = Traceui.Traceui(self.penicons,self.config,"Trace",self.graphicsView)
        self.traceui.setupUi(self.traceui)
        self.dockWidget.setWidget( self.traceui )

        self.timestampTraceui = Traceui.Traceui(self.penicons,self.config,self.experimentName+"-timestamps",self.timestampView)
        self.timestampTraceui.setupUi(self.timestampTraceui)
        self.timestampDockWidget.setWidget( self.timestampTraceui )
        self.dockWidgetList.append(self.timestampDockWidget)       
        self.fitWidget = FitUi.FitUi(self.traceui,self.config,self.experimentName)
        self.fitWidget.setupUi(self.fitWidget)
        self.dockWidgetFitUi.setWidget( self.fitWidget )
        self.dockWidgetList.append(self.dockWidgetFitUi )
        self.scanControlWidget = ScanControl.ScanControl(config,self.experimentName, self.plotWidgets.keys() )
        self.plotWidgets[None] =  self.graphicsView      # this is the default plotwindow
        self.scanControlWidget.setupUi(self.scanControlWidget)
        self.scanControlUi.setWidget(self.scanControlWidget )
        self.scanControlWidget.scansAveraged.hide()
        self.dockWidgetList.append(self.scanControlUi)
        self.tabifyDockWidget( self.scanControlUi, self.dockWidgetFitUi )
        self.tabifyDockWidget( self.timestampDockWidget, self.dockWidget)
        # Average View
        self.displayUi = AverageView(self.config,"testExperiment")
        self.displayUi.setupUi(self.displayUi)
        self.displayDock = QtGui.QDockWidget("Average")
        self.displayDock.setObjectName("Average")
        self.displayDock.setWidget( self.displayUi )
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea , self.displayDock)
        self.dockWidgetList.append(self.displayDock )
        if self.experimentName+'.MainWindow.State' in self.config:
            QtGui.QMainWindow.restoreState(self,self.config[self.experimentName+'.MainWindow.State'])
        self.updateProgressBar(0,1)
