'''
Created on Jul 8, 2014

@author: pmaunz
'''

from pyqtgraph.parametertree import Parameter
from PyQt4 import QtCore, uic

class Preferences(object):
    def __init__(self):
        self.printResolution = 1200
        self.printWidth = 0.4
        self.printX = 0.1
        self.printY = 0.1
        self.linewidth = 10
        
    def paramDef(self):
        return [{'name': 'Print Preferences', 'type': 'group', 'children': [
                        {'name': 'printResolution', 'field': 'printResolution', 'type': 'int', 'value': self.printResolution},
                        {'name': 'printWidth', 'field': 'printWidth', 'type': 'float', 'value': self.printWidth},
                        {'name': 'printX', 'field': 'printX', 'type': 'float', 'value': self.printX}, 
                        {'name': 'printY', 'field': 'printY', 'type': 'float', 'value': self.printY},
                        {'name': 'linewidth', 'field': 'linewidth', 'type': 'int', 'value': self.linewidth}] }]
        

Form, Base = uic.loadUiType(r'ui\Preferences.ui')
        
class PreferencesUi(Form, Base):
    def __init__(self, config, parent=None):
        Base.__init__(self,parent)
        Form.__init__(self)
        self.config = config
        self._preferences = config.get('GlobalPreferences',Preferences())
    
    def setupUi(self,MainWindow):
        Form.setupUi(self,MainWindow)
        self.treeWidget.setParameters( self.parameter() )
 
    def update(self,param, changes):
        """
        update the parameter, called by the signal of pyqtgraph parametertree
        """
        for param, _, data in changes:
            setattr( self._preferences, param.opts['field'], data)

    def saveConfig(self):
        self.config['GlobalPreferences'] = self._preferences

    def parameter(self):
        # re-create the parameters each time to prevent a exception that says the signal is not connected
        self._parameter = Parameter.create(name='Preferences', type='group',children=self._preferences.paramDef())     
        self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        return self._parameter    
    
    def preferences(self):
        return self._preferences    
