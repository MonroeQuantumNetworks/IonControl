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
        self.savePdf = False
        self.savePng = False
        self.doPrint = True
        self.saveSvg = True
        self.exportEmf = True
        self.exportPdf = True
        self.inkscapeExecutable = r'C:\Program Files\Inkscape\inkscape.exe'
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault('saveSvg', True)
        self.__dict__.setdefault('exportEmf', True)
        self.__dict__.setdefault('exportPdf', True)
        self.__dict__.setdefault('inkscapeExecutable', r'C:\Program Files\Inkscape\inkscape.exe')

    def paramDef(self):
        return [ {'name': 'resolution (dpi)', 'object': self, 'field': 'printResolution', 'type': 'int', 'value': self.printResolution},
                {'name': 'width (page width)', 'object': self, 'field': 'printWidth', 'type': 'float', 'value': self.printWidth},
                {'name': 'x (page width)', 'object': self, 'field': 'printX', 'type': 'float', 'value': self.printX}, 
                {'name': 'y (page height)', 'object': self, 'field': 'printY', 'type': 'float', 'value': self.printY},
                {'name': 'grid linewidth (px)', 'object': self, 'field': 'gridLinewidth', 'type': 'int', 'value': self.gridLinewidth},
                {'name': 'curve linewidth (px)', 'object': self, 'field': 'curveLinewidth', 'type': 'int', 'value': self.curveLinewidth},
                {'name': 'save pdf', 'object': self, 'field': 'savePdf', 'type': 'bool', 'value': self.savePdf},
                {'name': 'save svg', 'object': self, 'field': 'saveSvg', 'type': 'bool', 'value': self.saveSvg},
                {'name': 'print', 'object': self, 'field': 'doPrint', 'type': 'bool', 'value': self.doPrint},
                {'name': 'export emf', 'object': self, 'field': 'exportEmf', 'type': 'bool', 'value': self.saveSvg},
                {'name': 'export pdf', 'object': self, 'field': 'exportPdf', 'type': 'bool', 'value': self.saveSvg},
                {'name': 'inkscape executable', 'object': self, 'field': 'inkscapeExecutable', 'type': 'str', 'value': self.inkscapeExecutable}]


class GuiPreferences(object):
    def __init__(self):
        self.useCondensedGlobalTree = False

    def paramDef(self):
        return [ {'name': 'use condensed global tree', 'object': self, 'field': 'useCondensedGlobalTree', 'type': 'bool', 'value': self.useCondensedGlobalTree} ]


class Preferences(object):
    def __init__(self):
        self.printPreferences = PrintPreferences()
        self.guiPreferences = GuiPreferences()
        # persistence database
        
    def __setstate__(self, state):
        self.printPreferences = state.get('printPreferences', PrintPreferences())
        self.guiPreferences = state.get('guiPreferences', GuiPreferences())

    def paramDef(self):
        return [{'name': 'Print Preferences', 'type': 'group', 'children': self.printPreferences.paramDef()},
                {'name': 'Display Preferences (take effect on restart)', 'type': 'group', 'children': self.guiPreferences.paramDef()}]
        

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
