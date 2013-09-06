# -*- coding: utf-8 -*-
"""
Created on Thu Sep 05 20:31:16 2013

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui, QtCore

Form, Base = PyQt4.uic.loadUiType(r'ui\InputCalibrationUi.ui')
SheetForm, SheetBase = PyQt4.uic.loadUiType(r'ui\InputCalibrationChannel.ui')

import AnalogInputCalibration
from pyqtgraph.parametertree import Parameter, ParameterTree

class Settings:
    def __init__(self):
        pass
    
class ChannelSettings:
    def __init__(self):
        self.calibration = "Voltage"
        self.parameters = dict()  #  map from calibration to settings
        
class InputCalibrationChannel(SheetForm,SheetBase):
    def __init__(self, config, channel, parent=None):
        SheetBase.__init__(self,parent)
        SheetForm.__init__(self)
        self.config = config
        self.channel = channel
        self.settings = self.config.get("InputCalibration.{0}".format(channel),ChannelSettings())
        self.myCalibration = None
        self.treeWidget = None
    
    def setupUi(self,callback,MainWindow):
        SheetForm.setupUi(self,MainWindow) 
        self.calibrationsCombo.addItems( AnalogInputCalibration.AnalogInputCalibrationMap.keys() )   
        self.calibrationsCombo.currentIndexChanged["QString"].connect( self.onCalibrationChanged )
        self.callback = callback
        if self.settings.calibration:
            self.onCalibrationChanged(self.settings.calibration)
            self.calibrationsCombo.setCurrentIndex(self.calibrationsCombo.findText(self.settings.calibration))
      
    def onCalibrationChanged(self,calibration):  
        calibration = str(calibration)
        print "calibration changed to '{0}'".format(calibration)
        print AnalogInputCalibration.AnalogInputCalibrationMap
        print calibration in AnalogInputCalibration.AnalogInputCalibrationMap
        if self.myCalibration:
            print "save parameters", self.myCalibration.parameters.__dict__
            self.settings.parameters[self.settings.calibration] = self.myCalibration.parameters
        self.myCalibration = AnalogInputCalibration.AnalogInputCalibrationMap[calibration]() 
        if calibration in self.settings.parameters:
            print "restore parameters", self.settings.parameters[calibration].__dict__
            self.myCalibration.parameters = self.settings.parameters[calibration]
        if not self.treeWidget:
            self.param = Parameter.create(name='params', type='group', children=self.myCalibration.paramDef())
            self.treeWidget = ParameterTree()
            self.treeWidget.setParameters(self.param, showTop=False)
            self.verticalLayout.insertWidget(2,self.treeWidget)
            self.param.sigTreeStateChanged.connect(self.myCalibration.update, QtCore.Qt.UniqueConnection)
        else:
            print self.myCalibration.paramDef()
            self.param = Parameter.create(name='params', type='group', children=self.myCalibration.paramDef())
            self.treeWidget.setParameters(self.param, showTop=False)
            self.param.sigTreeStateChanged.connect(self.myCalibration.update, QtCore.Qt.UniqueConnection)
        self.settings.calibration = calibration
        self.callback( self.channel, self.myCalibration )
            
    def onClose(self):
        if self.myCalibration:
            self.settings.parameters[self.settings.calibration] = self.myCalibration.parameters
        self.config["InputCalibration.{0}".format(self.channel)] = self.settings
        

class InputCalibrationUi(Form,Base):
    def __init__(self, config, numChannels, parent=None):
        Base.__init__(self,parent)
        Form.__init__(self)
        self.config = config
        self.numChannels = numChannels
        self.settings = self.config.get("InputCalibration.Settings",Settings())
        self.calibrations = [None]*numChannels
        self.widgetList = list()
    
    def setupUi(self,MainWindow):
        Form.setupUi(self,MainWindow)
        self.channelSpinBox.setMaximum( self.numChannels-1 )
        for i in range(self.numChannels):
            ui = InputCalibrationChannel(self.config,i)
            ui.setupUi(self.updateCalibration, ui)
            self.stackedWidget.insertWidget(i,ui)
            self.calibrations.append(ui.myCalibration)
            self.widgetList.append(ui)
        self.stackedWidget.setCurrentIndex(0)

    def updateCalibration(self, channel, calibration):
        self.calibrations[channel] = calibration

    def onClose(self):
        self.config["InputCalibration.Settings"] = self.settings
        for widget in self.widgetList:
            widget.onClose()

if __name__=="__main__":
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = InputCalibrationUi(config,4)
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
