'''
Created on Aug 31, 2014

@author: pmaunz
'''

import PyQt4.uic
from PyQt4 import QtCore
from functools import partial
from persist.ValueHistory import ValueHistoryStore
from modules.PyqtUtility import updateComboBoxItems
from datetime import datetime
from collections import defaultdict
import logging
from uiModules.GenericTableModel import GenericTableModel
from modules.GuiAppearance import restoreGuiState, saveGuiState   #@UnresolvedImport
from modules.magnitude import mg
from modules.NamedTimespan import getRelativeDatetime, timespans
from dateutil.tz import tzlocal

Form, Base = PyQt4.uic.loadUiType(r'ui\ValueHistory.ui')


class Parameters(object):
    def __init__(self):
        self.space = None
        self.parameter = None
        self.fromTime = datetime(2014,1,1)
        self.spaceParamCache = dict()

class ValueHistoryUi(Form,Base):
    def __init__(self, config, dbConnection, parent=None):
        Base.__init__(self,parent)
        Form.__init__(self)
        self.config = config
        self.parameters = self.config.get("ValueHistory.parameters",Parameters())
        self.dbConnection = dbConnection
        self.connection = ValueHistoryStore(dbConnection)
        self.connection.open_session()
        self.cache = dict()
    
    def setupUi(self,MainWindow):
        Form.setupUi(self,MainWindow)
        self.comboBoxSpace.currentIndexChanged[QtCore.QString].connect( self.onSpaceChanged  )
        self.comboBoxParam.currentIndexChanged[QtCore.QString].connect( partial(self.onValueChangedString, 'parameter') )    
        self.loadButton.clicked.connect( self.onLoad )       
        self.namedTimespanComboBox.addItems( ['Select timespan ...']+timespans )
        self.namedTimespanComboBox.currentIndexChanged[QtCore.QString].connect( self.onNamedTimespan )
        self.onRefresh()
        if self.parameters.space is not None:
            self.comboBoxSpace.setCurrentIndex( self.comboBoxSpace.findText(self.parameters.space ))
        if self.parameters.parameter is not None:
            self.comboBoxParam.setCurrentIndex( self.comboBoxParam.findText(self.parameters.parameter ))
        if self.parameters.fromTime is not None:
            self.dateTimeEditFrom.setDateTime( self.parameters.fromTime )
        self.dateTimeEditFrom.dateTimeChanged.connect( partial(self.onValueChangedDateTime, 'fromTime')  )
        self.toolButtonRefresh.clicked.connect( self.onRefresh )
        self.onSpaceChanged(self.parameters.space)
        self.dataModel = GenericTableModel(self.config, list(), "ValueHistory", ["Date","Value"], [lambda t: t.astimezone(tzlocal()).strftime('%Y-%m-%d %H:%M:%S'), str])
        self.tableView.setModel( self.dataModel )
        restoreGuiState( self, self.config.get('ValueHistory.guiState'))
        
    def onNamedTimespan(self, name):
        dt = getRelativeDatetime(str(name), None)
        if dt is not None:
            self.parameters.fromTime = dt
            self.dateTimeEditFrom.setDateTime( self.parameters.fromTime )
            self.namedTimespanComboBox.setCurrentIndex(0)

    def onValueChangedString(self, param, value):
        setattr( self.parameters, param, str(value) )

    def onValueChangedDateTime(self, param, value):
        setattr( self.parameters, param, value.toPyDateTime() )

    def saveConfig(self):
        self.config["ValueHistory.parameters"] = self.parameters
        self.config['ValueHistory.guiState'] = saveGuiState( self )
        
    def onRefresh(self):
        self.parameterNames = defaultdict( list )
        for (space,source) in self.connection.refreshSourceDict().keys():
            self.parameterNames[space].append(source)
        updateComboBoxItems( self.comboBoxSpace, sorted(self.parameterNames.keys()) )
        updateComboBoxItems( self.comboBoxParam, sorted(self.parameterNames[self.parameters.space]) )
        
    def onSpaceChanged(self, newSpace):
        newSpace = str(newSpace)
        if self.parameters.space is not None and self.parameters.parameter is not None:
            self.parameters.spaceParamCache[self.parameters.space] = self.parameters.parameter
        self.parameters.space = newSpace
        self.parameters.parameter = self.parameters.spaceParamCache.get( self.parameters.space, self.parameterNames[self.parameters.space][0] if len(self.parameterNames[self.parameters.space])>0 else None )
        updateComboBoxItems( self.comboBoxParam, sorted(self.parameterNames[self.parameters.space]) )
        if self.parameters.parameter is not None:
            self.comboBoxParam.setCurrentIndex( self.comboBoxParam.findText(self.parameters.parameter ))
               
    def onLoad(self):
        self.doLoad( self.parameters.space, self.parameters.parameter, self.parameters.fromTime )

    def doLoad(self, space, parameter, fromTime ):
        result = self.connection.getHistory( space, parameter, fromTime , datetime.now() )
        if not result:
            logging.getLogger(__name__).warning("Database query returned empty set")
        elif len(result)>0:
            self.data = [(e.upd_date, mg(e.value, e.unit)) for e in reversed(result)]
            self.dataModel.setDataTable(self.data)
                
           
