# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 20:15:47 2013

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui, QtCore

from pyqtgraph.parametertree import Parameter, ParameterTree

ConfigForm, ConfigBase = PyQt4.uic.loadUiType(r'ui\ExternalScannedParametersConfig.ui')

class ConfigUi(ConfigForm,ConfigBase):
    def __init__(self, paramname, parent=None):
        ConfigBase.__init__(self,parent)
        ConfigForm.__init__(self)
        self.paramname = paramname
        self.param = None
        self.treeWidget = None
    
    def setupUi(self,MainWindow,default):
        ConfigForm.setupUi(self,MainWindow)
        self.verticalLayout.addStretch()
        self.instrumentLineEdit.setText(default[0])
        self.enableCheckBox.setChecked(default[1])
        
    def update(self,parameter):
        if parameter:
            if not self.treeWidget:
                self.param = Parameter.create(name='params', type='group', children=parameter.paramDef())
                self.treeWidget = ParameterTree()
                self.treeWidget.setParameters(self.param, showTop=False)
                self.verticalLayout.insertWidget(2,self.treeWidget)
                self.param.sigTreeStateChanged.connect(parameter.update, QtCore.Qt.UniqueConnection)
            else:
                self.treeWidget.setVisible(True)
                self.param.sigTreeStateChanged.connect(parameter.update, QtCore.Qt.UniqueConnection)
        else:
            if self.treeWidget:
                self.treeWidget.setVisible(False)

if __name__ == "__main__":
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = ConfigUi()
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())

