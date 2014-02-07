'''
Created on Feb 6, 2014

@author: pmaunz
'''
from PyQt4 import QtCore, QtGui
import sip

api2 = sip.getapi("QVariant")==2

    
class LogicAnalyzerTraceTableModel(QtCore.QAbstractTableModel):
    def __init__(self, config, signalTableModel, parent=None, *args): 
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.config = config 
        self.signalTableModel = signalTableModel
        self.dataLookup = { (QtCore.Qt.DisplayRole,1): lambda row: self.pulseData[row][0],
                            (QtCore.Qt.DisplayRole,0): lambda row: self.pulseData[row][0]-self.referenceTime
                     }
        self.pulseData = None
        self.referenceTime = 0
        self.onEnabledChannelsChanged()
        self.signalTableModel.enableChanged.connect( self.onEnabledChannelsChanged )
        
    def setPulseData(self, pulseData):
        self.beginResetModel()
        self.pulseData = list(sorted(pulseData.iteritems()))
        self.headerDataChanged.emit( QtCore.Qt.Horizontal, 0, len(self.enabledSignalLookup) )
        self.endResetModel()
        
    def onEnabledChannelsChanged(self):
        self.beginResetModel()
        self.enabledSignalLookup = list()
        for channel, enabled in enumerate(self.signalTableModel.enabledList):
            if enabled:
                self.enabledSignalLookup.append(channel)
        self.endResetModel()
        self.headerDataChanged.emit( QtCore.Qt.Horizontal, 0, len(self.enabledSignalLookup) )
        
    def setReferenceTime(self, time):
        self.referenceTime = time
        
    def rowCount(self, parent=QtCore.QModelIndex()): 
        return len(self.pulseData) if self.pulseData else 0
        
    def columnCount(self, parent=QtCore.QModelIndex()): 
        return 2 + len(self.enabledSignalLookup)
 
    colorLookup = { False: QtGui.QColor(QtCore.Qt.red), True: QtGui.QColor(QtCore.Qt.green), None: QtGui.QColor(QtCore.Qt.white) }
    def pulseDataLookup(self, timestep, signal):
        return self.colorLookup[self.pulseData[timestep][1].get(signal,None)]
    
    def data(self, index, role): 
        if index.isValid():
            if index.column()>1 and role==QtCore.Qt.BackgroundColorRole:
                return self.pulseDataLookup(index.row(), self.enabledSignalLookup[index.column()-2])
            return self.dataLookup.get((role,index.column()),lambda row: None)(index.row())
        return None
        
    def flags(self, index ):
        return  QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsEnabled

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Horizontal): 
                if section==0:
                    return 'Time'
                if section==1:
                    return 'relative time'
                return self.signalTableModel.channelName(self.enabledSignalLookup[section-2])
        return None #QtCore.QVariant()
    
    def saveConfig(self):
        self.config['LogicAnalyzer.EnabledChannels'] = self.enabledList
        