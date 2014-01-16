from PyQt4 import QtGui, QtCore
from functools import partial
from CountEvaluation import EvaluationAlgorithms

class EvaluationTableModel( QtCore.QAbstractTableModel):
    dataChanged = QtCore.pyqtSignal( object, object )
    headerDataLookup = ['Counter','Evaluation','Name','Hist', 'Plot' ]
    def __init__(self, updateSaveStatus, plotnames=None, evalList=None, parent=None):
        super(EvaluationTableModel, self).__init__(parent)
        if evalList:
            self.evalList = evalList
        else:
            self.evalList = list()
        self.plotnames = plotnames
        self.updateSaveStatus = updateSaveStatus
        self.evalAlgorithmList = list()
        self.setDataLookup =  {  (QtCore.Qt.EditRole,0): self.setCounter,
                                 (QtCore.Qt.EditRole,1): self.setAlgorithm,
                                 (QtCore.Qt.EditRole,2): self.setDataName,
                                 (QtCore.Qt.EditRole,4): self.setPlotName,
                                 (QtCore.Qt.CheckStateRole,3): self.setShowHistogram,
                                }
        self.dataLookup = {  (QtCore.Qt.DisplayRole,0): lambda self, row: self.evalList[row].counter,
                             (QtCore.Qt.DisplayRole,1): lambda self, row: self.evalList[row].evaluation,
                             (QtCore.Qt.DisplayRole,2): lambda self, row: self.evalList[row].name,
                             (QtCore.Qt.DisplayRole,4): lambda self, row: self.evalList[row].plotname,
                             (QtCore.Qt.EditRole,0):    lambda self, row: self.evalList[row].counter,
                             (QtCore.Qt.EditRole,1):    lambda self, row: self.evalList[row].evaluation,
                             (QtCore.Qt.EditRole,2):    lambda self, row: self.evalList[row].name,
                             (QtCore.Qt.EditRole,4):    lambda self, row: self.evalList[row].plotname,
                             (QtCore.Qt.CheckStateRole,3): lambda self, row: QtCore.Qt.Checked if self.evalList[row].showHistogram else QtCore.Qt.Unchecked,
                             }
        
    def setData(self, index, value, role):
        return self.setDataLookup.get((role,index.column()), lambda index, value: False )(index, value)

    def choice(self, index):
        return {1:EvaluationAlgorithms.keys(),4:self.plotnames}[index]
        
    def setEvalList(self, evalList, evalAlgorithmList):
        self.beginResetModel()
        self.evalList = evalList
        self.evalAlgorithmList = evalAlgorithmList
        self.endResetModel()
        
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.evalList)
    
    def columnCount(self,  parent=QtCore.QModelIndex()):
        return 5
    
    def data(self, index, role): 
        if index.isValid():
            return self.dataLookup.get((role,index.column()),lambda self, row: None)(self,index.row())
        return None
        
    def flags(self, index ):
        if index.column() in [0,1,2,4]:
            return  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable
        if index.column()==3:
            return  QtCore.Qt.ItemIsSelectable |  QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled
        return  QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role ):
        if (role == QtCore.Qt.DisplayRole):
            if (orientation == QtCore.Qt.Vertical): 
                return str(section)
            elif (orientation == QtCore.Qt.Horizontal): 
                return self.headerDataLookup[section]
        return None 

    def setCounter(self,index,value):
        self.evalList[index.row()].counter, ok = value.toInt()
        self.dataChanged.emit( index, index )
        return True      

    def setShowHistogram(self,index,value):
        self.evalList[index.row()].showHistogram = (value == QtCore.Qt.Checked )
        self.dataChanged.emit( index, index )
        return True      
                
    def setValue(self, index, value):
        self.setData( index, value, QtCore.Qt.EditRole)
                
    def setDataName(self, index, name):
        name = str(name.toString()).strip()
        self.evalList[index.row()].name = name
        self.evalAlgorithmList[index.row()].setSettingsName(name)
        self.dataChanged.emit( index, index )
        return True
    
    def setPlotName(self, index, plotname):
        self.evalList[index.row()].plotname = str(plotname)
        self.dataChanged.emit( index, index )
        return True
        
    def setAlgorithm(self, index, algorithm):
        algorithm = str(algorithm)
        eval = self.evalList[index.row()]
        if algorithm!=eval.evaluation:
            eval.settingsCache[eval.evaluation] = eval.settings
            eval.evaluation = algorithm
            algo = EvaluationAlgorithms[eval.evaluation]()
            algo.subscribe( self.updateSaveStatus )   # track changes of the algorithms settings so the save status is displayed correctly
            if eval.evaluation in eval.settingsCache:
                eval.settings = eval.settingsCache[eval.evaluation]
            else:
                eval.settings = dict()
            algo.setSettings( eval.settings, eval.name )
            self.evalAlgorithmList[index.row()] = algo     
            self.dataChanged.emit(index, index) 
