'''
Created on Aug 30, 2014

@author: pmaunz
'''

from ExternalParameterSelection import SelectionUi
from pyqtgraph.parametertree import ParameterTree

class InstrumentLoggingSelection( SelectionUi ):
    def __init__(self, config, classdict, instancename="ExternalParameterSelection.ParametersSequence", newDataSlot=None, plotNames=None, parent=None, instrumentLoggingHandler=None ):
        super(InstrumentLoggingSelection, self).__init__(config, classdict, instancename, newDataSlot, parent)
        self.instrumentLoggingHandler = instrumentLoggingHandler
        self.current = None
        
    def setupUi(self,MainWindow):
        super(InstrumentLoggingSelection, self).setupUi(MainWindow)
        self.loggingHandlerTreeWidget = ParameterTree(self.splitter)
        self.loggingHandlerTreeWidget.setObjectName("loggingHandlerTreeWidget")
        self.loggingHandlerTreeWidget.headerItem().setText(0, "1")
        self.loggingHandlerTreeWidget.header().setVisible(False)

    def onActiveInstrumentChanged(self, modelIndex, modelIndex2 ):
        self.current = self.parameters.at(modelIndex.row()).name
        super(InstrumentLoggingSelection, self).onActiveInstrumentChanged( modelIndex, modelIndex2 )          
        self.loggingHandlerTreeWidget.setParameters( self.instrumentLoggingHandler.parameter(self.current) )
        
    def refreshParamTree(self):
        if self.current is not None:
            self.loggingHandlerTreeWidget.setParameters( self.instrumentLoggingHandler.parameter(self.current) )
        
        
