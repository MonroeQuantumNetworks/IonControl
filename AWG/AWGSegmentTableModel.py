"""
Created on 09 Dec 2015 at 8:38 PM

author: jmizrahi
"""
from PyQt4 import QtCore, QtGui

from modules.Expression import Expression
from modules.firstNotNone import firstNotNone
from modules.enum import enum
from modules.MagnitudeParser import isIdentifier
import sip
api2 = sip.getapi("QVariant")==2

class AWGSegmentTableModel(QtCore.QAbstractTableModel):
    segmentChanged = QtCore.pyqtSignal(int, int, int, str) #channel, row, column, value
    def __init__(self, channel, settings, globalDict, parent=None, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.channel = channel
        self.settings = settings
        self.globalDict = globalDict
        self.column = enum('amplitude', 'duration')
        self.dataLookup = {
            (QtCore.Qt.DisplayRole, self.column.amplitude): lambda row: self.segmentList[row]['amplitude'],
            (QtCore.Qt.DisplayRole, self.column.duration): lambda row: self.segmentList[row]['duration'],
            (QtCore.Qt.EditRole, self.column.amplitude): lambda row: self.segmentList[row]['amplitude'],
            (QtCore.Qt.EditRole, self.column.duration): lambda row: self.segmentList[row]['duration']
            }
        self.setDataLookup = {
            (QtCore.Qt.EditRole, self.column.amplitude): lambda index, value: self.setValue(index, value),
            (QtCore.Qt.EditRole, self.column.duration): lambda index, value: self.setValue(index, value)
            }
        self.flagsLookup = {
            self.column.amplitude: QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable,
            self.column.duration: QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable
            }

    @QtCore.pyqtProperty(list)
    def segmentList(self):
        return self.settings.channelSettingsList[self.channel]['segmentList']

    def flags(self, index):
        return self.flagsLookup[index.column()]

    def setValue(self, index, value):
        row = index.row()
        column = index.column()
        strvalue = str((value if api2 else value.toString()) if isinstance(value, QtCore.QVariant) else value)
        if strvalue in self.globalDict:
            logger.warning("'{0}' is already a global variable name".format(strvalue))
            return False
        elif not isIdentifier(strvalue):
            logger.warning("'{0}' is not a valid variable name".format(strvalue))
            return False
        else:
            if column==self.column.amplitude:
                self.segmentList[row]['amplitude'] = strvalue
            elif column==self.column.duration:
                self.segmentList[row]['duration'] = strvalue
            self.dataChanged.emit(index, index)
            self.segmentChanged.emit(self.channel, row, column, strvalue)
            self.settings.saveIfNecessary()
            return True

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.segmentList)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return 2

    def data(self, index, role):
        if index.isValid():
            return self.dataLookup.get((role, index.column()), lambda row: None)(index.row())
        return None

    def setData(self, index, value, role):
        return self.setDataLookup.get((role,index.column()), lambda index, value: False )(index, value)

    def headerData(self, section, orientation, role):
        if orientation==QtCore.Qt.Vertical:
            return str(section)
        elif orientation==QtCore.Qt.Horizontal and role==QtCore.Qt.DisplayRole:
            if section==self.column.amplitude:
                return 'Amplitude'
            elif section==self.column.duration:
                return 'Duration'

    def addSegment(self):
        row = len(self.segmentList)
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self.segmentList.append({'amplitude':'v{0}'.format(row), 'duration':'t{0}'.format(row)})
        self.settings.saveIfNecessary()
        self.endInsertRows()

    def removeSegment(self, row):
        self.beginRemoveRows(QtCore.QModelIndex(), row, row)
        del self.segmentList[row]
        self.settings.saveIfNecessary()
        self.endRemoveRows()

