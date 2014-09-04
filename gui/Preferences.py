'''
Created on Jul 8, 2014

@author: pmaunz
'''

from pyqtgraph.parametertree import Parameter
from PyQt4 import QtCore, uic


class PrintPreferences(object):
    def __init__(self):
        self.printResolution = 1200
        self.printWidth = 0.4
        self.printX = 0.1
        self.printY = 0.1
        self.gridLinewidth = 8
        self.curveLinewidth = 8
        self.savePdf = True
        self.savePng = False
        self.doPrint = True

    def paramDef(self):
        return [ {'name': 'resolution (dpi)', 'object': self, 'field': 'printResolution', 'type': 'int', 'value': self.printResolution},
                {'name': 'width (page width)', 'object': self, 'field': 'printWidth', 'type': 'float', 'value': self.printWidth},
                {'name': 'x (page width)', 'object': self, 'field': 'printX', 'type': 'float', 'value': self.printX}, 
                {'name': 'y (page height)', 'object': self, 'field': 'printY', 'type': 'float', 'value': self.printY},
                {'name': 'grid linewidth (px)', 'object': self, 'field': 'gridLinewidth', 'type': 'int', 'value': self.gridLinewidth},
                {'name': 'curve linewidth (px)', 'object': self, 'field': 'curveLinewidth', 'type': 'int', 'value': self.curveLinewidth},
                {'name': 'save pdf', 'object': self, 'field': 'savePdf', 'type': 'bool', 'value': self.savePdf},
                {'name': 'save png', 'object': self, 'field': 'savePng', 'type': 'bool', 'value': self.savePng},
                {'name': 'print', 'object': self, 'field': 'doPrint', 'type': 'bool', 'value': self.doPrint}]    

class DatabasePreferences(object):
    def __init__(self):
        self.databaseHost = None
        self.databaseName = None
        self.databaseUser = None
        self.databasePassword = None

    def paramDef(self):
        return [ {'name': 'Hostname', 'object': self, 'field': 'databaseHost', 'type': 'str', 'value': self.databaseHost},
                {'name': 'Database name', 'object': self, 'field': 'databaseName', 'type': 'str', 'value': self.databaseName},
                {'name': 'Username', 'object': self, 'field': 'databaseUser', 'type': 'str', 'value': self.databaseUser},
                {'name': 'Password', 'object': self, 'field': 'databasePassword', 'type': 'str', 'value': self.databasePassword}]

class Preferences(object):
    def __init__(self):
        self.printPreferences = PrintPreferences()
        self.databasePreferences = DatabasePreferences()
        # persistence database
               
    def paramDef(self):
        return [{'name': 'Print Preferences', 'type': 'group', 'children': self.printPreferences.paramDef() },
                {'name': 'Persistence Preferences', 'type': 'group', 'children': self.databasePreferences.paramDef() } ]
        

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
            setattr( param.opts['object'], param.opts['field'], data)

    def saveConfig(self):
        self.config['GlobalPreferences'] = self._preferences

    def parameter(self):
        # re-create the parameters each time to prevent a exception that says the signal is not connected
        self._parameter = Parameter.create(name='Preferences', type='group',children=self._preferences.paramDef())     
        self._parameter.sigTreeStateChanged.connect(self.update, QtCore.Qt.UniqueConnection)
        return self._parameter    
    
    def preferences(self):
        return self._preferences    
