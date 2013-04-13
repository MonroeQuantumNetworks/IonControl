# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 20:15:47 2013

@author: pmaunz
"""

import PyQt4.uic
from PyQt4 import QtGui, QtCore

import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType

ConfigForm, ConfigBase = PyQt4.uic.loadUiType(r'ui\ExternalScannedParametersConfig.ui')

class ConfigUi(ConfigForm,ConfigBase):
    def __init__(self, paramname, parent=None):
        ConfigBase.__init__(self,parent)
        ConfigForm.__init__(self)
        self.paramname = paramname
        self.param = None
        self.treeWidget = None
    
    def setupUi(self,MainWindow):
        ConfigForm.setupUi(self,MainWindow)
        self.verticalLayout.addStretch()
        
    def update(self,parameter):
        if parameter:
            if not self.treeWidget:
                self.param = Parameter.create(name='params', type='group', children=parameter.paramDef())
                self.treeWidget = ParameterTree()
                self.treeWidget.setParameters(self.param, showTop=False)
                self.verticalLayout.insertWidget(1,self.treeWidget)
                self.param.sigTreeStateChanged.connect(parameter.update)
            else:
                self.treeWidget.setVisible(True)
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

