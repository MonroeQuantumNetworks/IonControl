import PyQt4.uic
from PyQt4 import QtGui, QtCore, QtSvg

import logging

Form, Base = PyQt4.uic.loadUiType(r'ui\RepetitionRateWidget.ui')

class RepetitionRateWidget(Form, Base):
    def __init__(self,settings,pulserHardware,config,parent=None):
        Base.__init__(self,parent)
        Form.__init__(self)
        self.settings = settings
        self.pulser = pulserHardware
        self.config = config
    
    def setupUi(self):
        Form.setupUi(self,self)
