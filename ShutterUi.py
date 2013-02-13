# -*- coding: utf-8 -*-
"""
Created on Sat Feb 09 22:00:58 2013

@author: pmaunz
"""
from PyQt4 import QtGui, QtCore
import PyQt4.uic
import ShutterHardwareTableModel

ShutterForm, ShutterBase = PyQt4.uic.loadUiType(r'ui\Shutter.ui')

class ShutterUi(ShutterForm, ShutterBase):
    onColor =  QtGui.QColor(QtCore.Qt.green)
    offColor =  QtGui.QColor(QtCore.Qt.red)
    def __init__(self,pulserHardware,outputname,parent=None):
        ShutterBase.__init__(self,parent)
        ShutterForm.__init__(self,parent)
        self.shutterdict = dict()
        self.pulserHardware = pulserHardware
        self.outputname = outputname
        
    def setupUi(self,parent):
        ShutterForm.setupUi(self,parent)
        self.shutterTableModel = ShutterHardwareTableModel.ShutterHardwareTableModel(self.shutterdict,self.pulserHardware,self.outputname)
        self.shutterTableModel.offColor = self.offColor
        self.shutterTableView.setModel(self.shutterTableModel)
        self.shutterTableView.resizeColumnsToContents()
        self.shutterTableView.resizeRowsToContents()
        self.shutterTableView.clicked.connect(self.shutterTableModel.onClicked)

        
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ui = ShutterUi()
    ui.setupUi(ui)
    ui.show()
    sys.exit(app.exec_())
