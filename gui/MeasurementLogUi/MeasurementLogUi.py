'''
Created on Nov 21, 2014

@author: pmaunz
'''

from PyQt4 import QtCore, QtGui
import PyQt4.uic
from persist.MeasurementLog import MeasurementContainer
from gui.MeasurementLogUi.MeasurementTableModel import MeasurementTableModel
from gui.MeasurementLogUi.ResultTableModel import ResultTableModel 
from gui.MeasurementLogUi.StudyTableModel import StudyTableModel
from gui.MeasurementLogUi.ParameterTableModel import ParameterTableModel
from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate
from datetime import datetime, time, timedelta
from _functools import partial
from modules.firstNotNone import firstNotNone
from modules.Utility import unique
from gui.MeasurementLogUi.ScanNameTableModel import ScanNameTableModel
from modules.PyqtUtility import saveColumnWidth, restoreColumnWidth,\
    updateComboBoxItems
import weakref
import logging
import pytz
import numpy
from trace.Trace import Trace
from trace.PlottedTrace import PlottedTrace
from modules import WeakMethod

Form, Base = PyQt4.uic.loadUiType(r'ui\MeasurementLog.ui')



class Settings:
    def __init__(self):
        self.timespan = 0
        self.fromDateTimeEdit = datetime.combine(datetime.now().date(), time())
        self.toDateTimeEdit = datetime.combine((datetime.now()+timedelta(days=1)).date(), time())
        self.extraColumns = list()
        self.filterByScanName = False
        self.plotXAxis = None
        self.plotYAxis = None
        self.plotWindow = None
        self.xUnit = None
        self.yUnit = None
        
    def __setstate__(self, state):
        self.__dict__ = state
        self.__dict__.setdefault( 'timespan', 0)
        self.__dict__.setdefault( 'fromDateTimeEdit', datetime.combine(datetime.now().date(), time()))
        self.__dict__.setdefault( 'toDateTimeEdit', datetime.combine((datetime.now()+timedelta(days=1)).date(), time()))
        self.__dict__.setdefault( 'extraColumns', list())
        self.__dict__.setdefault( 'filterByScanName', False)
        self.__dict__.setdefault( 'plotXAxis', None)
        self.__dict__.setdefault( 'plotYAxis', None)
        self.__dict__.setdefault( 'plotWindow', None)

class MeasurementLogUi(Form, Base ):
    timespans = ['Today','Three days','One week','One month', 'Three month', 'One year', 'All', 'Custom']
    mySplitters = ['splitterHorizontal', "splitterVertical", "splitterHorizontalParam", "splitterLeftVertical" ]
    myTableViews = ["measurementTableView", "resultTableView", "studyTableView", "parameterTableView", "scanNameTableView"]
    def __init__(self,config,parent=None):
        Form.__init__(self)
        Base.__init__(self,parent)
        self.config = config
        self.configname = 'MeasurementLog'
        self.settings = self.config.get(self.configname,Settings())
        self.container = MeasurementContainer("postgresql://python:yb171@localhost/ioncontrol")
        self.container.open()
        self.fromToTimeLookup = [ lambda now: (datetime.combine(now.date(), time()), datetime.combine(now + timedelta(days=1), time())),              # today
                           lambda now: (datetime.combine(now - timedelta(days=3), time()),  datetime.combine(now + timedelta(days=1), time())),  # three days ago
                           lambda now: (datetime.combine(now - timedelta(days=7), time()),  datetime.combine(now + timedelta(days=1), time())),  # one week
                           lambda now: (datetime.combine(now - timedelta(days=30), time()), datetime.combine(now + timedelta(days=1), time())),   # 30 days
                           lambda now: (datetime.combine(now - timedelta(days=90), time()), datetime.combine(now + timedelta(days=1), time())),   # 90 days
                           lambda now: (datetime.combine(now - timedelta(years=1), time()), datetime.combine(now + timedelta(days=1), time())),   # 1 year
                           lambda now: (datetime(2014,11,1,0,0),  datetime.combine(now + timedelta(days=1), time())),  # all
                           lambda now: (self.settings.fromDateTimeEdit, self.settings.toDateTimeEdit)
                           ]
        self.sourceLookup = { 'measurement': lambda measurement, space, name: (getattr( measurement, name ),None,None),
                              'parameter': self.getParameter,
                              'result': self.getResult  }        
        self.currentMeasurement = None
        self.traceuiLookup = dict()        # the measurements should insert their traceui into this dictionary
        self.cache = dict()

    def addTraceui(self, scan, traceui ):
        self.traceuiLookup[scan] = traceui 
        self.plotWindowIndex = dict( (("{0}.{1}".format(key, item), (ui, item, d["view"])) for key,ui in self.traceuiLookup.iteritems() for item, d in ui.graphicsViewDict.iteritems()) )
        updateComboBoxItems( self.windowComboBox, sorted(self.plotWindowIndex.keys()), self.settings.plotWindow )
        self.settings.plotWindow = firstNotNone( self.settings.plotWindow, str(self.windowComboBox.currentText()) )

    def setupUi(self, parent):
        Form.setupUi(self,parent)
        # measurement Table
        self.measurementModel = MeasurementTableModel(self.container.measurements, self.settings.extraColumns, self.traceuiLookup, self.container)
        self.measurementTableView.setModel( self.measurementModel )
        # result Table
        self.resultModel = ResultTableModel( list(), self.container )
        self.resultTableView.setModel( self.resultModel )
        # study table
        self.studyModel = StudyTableModel( list(), self.container )
        self.studyTableView.setModel( self.studyModel )
        # parameter table
        self.parameterModel = ParameterTableModel( list(), self.container )
        self.parameterTableView.setModel( self.parameterModel )
        magnitudeDelegate = MagnitudeSpinBoxDelegate()
        self.parameterTableView.setItemDelegateForColumn( 2, magnitudeDelegate )
        # scanNames table
        self.scanNameTableModel = ScanNameTableModel( self.container.scanNames, self.container)
        self.scanNameTableView.setModel( self.scanNameTableModel )
        self.scanNameTableModel.scanNameFilterChanged.connect( self.onFilterSelection )
        # Context Menu for ResultsTable
        self.resultTableView.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.addResultToMeasurementAction = QtGui.QAction( "add as column to measurement" , self)
        self.addResultToMeasurementAction.triggered.connect( self.onAddResultToMeasurement  )
        self.resultTableView.addAction( self.addResultToMeasurementAction )
        # Context Menu for Measurements Table
        self.measurementTableView.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.removeColumnAction = QtGui.QAction( "remove selected column" , self)
        self.removeColumnAction.triggered.connect( self.onRemoveMeasurementColumn  )
        self.measurementTableView.addAction( self.removeColumnAction )
        # Context Menu for Parameters Table
        self.parameterTableView.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        self.addManualParameterAction = QtGui.QAction( "add manual parameter" , self)
        self.addManualParameterAction.triggered.connect( self.parameterModel.addManualParameter  )
        self.parameterTableView.addAction( self.addManualParameterAction )
        self.addParameterToMeasurementAction = QtGui.QAction( "add as column to measurement" , self)
        self.addParameterToMeasurementAction.triggered.connect( self.onAddParameterToMeasurement )
        self.parameterTableView.addAction( self.addParameterToMeasurementAction )
        # restore splitter positions
        for splitter in self.mySplitters:
            name = self.configname+"."+splitter
            if name in self.config:
                getattr(self, splitter).restoreState( self.config[name] )
        self.timespanComboBox.addItems( self.timespans )
        self.timespanComboBox.setCurrentIndex( self.settings.timespan )
        self.timespanComboBox.currentIndexChanged[int].connect( self.onChangeTimespan )
        self.container.beginInsertMeasurement.subscribe( self.measurementModel.beginInsertRows )
        self.container.endInsertMeasurement.subscribe( self.measurementModel.endInsertRows )  
        self.container.measurementsUpdated.subscribe( self.measurementModel.setMeasurements  )
        self.measurementTableView.selectionModel().currentChanged.connect( self.onActiveInstrumentChanged )
        self.refreshButton.clicked.connect( self.onFilterRefresh )
        # DateTimeEdit
        self.fromDateTimeEdit.setDateTime( self.settings.fromDateTimeEdit )
        self.toDateTimeEdit.setDateTime( self.settings.toDateTimeEdit )
        self.fromDateTimeEdit.dateTimeChanged.connect( partial( self.setDateTimeEdit, 'fromDateTimeEdit') )
        self.toDateTimeEdit.dateTimeChanged.connect( partial( self.setDateTimeEdit, 'toDateTimeEdit') )
        self.plainTextEdit.editingFinished.connect( self.onCommentFinished )
        self.onFilterRefresh()
        # restore ColumnWidth
        for tableView in self.myTableViews:
            restoreColumnWidth( getattr(self,tableView), self.config.get( self.configname+"."+tableView, list() ) )
        self.scanNameFilterButton.clicked.connect( self.onFilterButton )
        self.updateComboBoxes()
        self.plotButton.clicked.connect( self.onCreatePlot )
        self.updatePlotButton.clicked.connect( self.onUpdatePlot )
        self.updateAllPlotsButton.clicked.connect( self.onUpdateAll )
        self.xComboBox.currentIndexChanged[QtCore.QString].connect( partial(self.onComboBoxChanged, 'plotXAxis') )
        self.yComboBox.currentIndexChanged[QtCore.QString].connect( partial(self.onComboBoxChanged, 'plotYAxis') )
        self.windowComboBox.currentIndexChanged[QtCore.QString].connect( partial(self.onComboBoxChanged, 'plotWindow') )
        
    def onComboBoxChanged(self, attr, value):
        setattr( self.settings, attr, str(value) )
        
    def onFilterSelection(self, scanNames ):
        if self.settings.filterByScanName:
            self.container.setScanNameFilter( [name for name, enabled in scanNames.iteritems() if enabled] if self.settings.filterByScanName else None  )            
        
    def onFilterButton(self, value):
        self.settings.filterByScanName = value
        self.container.setScanNameFilter( [name for name, enabled in self.scanNameTableModel.scanNames.iteritems() if enabled] if self.settings.filterByScanName else None )
        
    def onAddParameterToMeasurement(self):
        if self.currentMeasurement is not None:
            for index in sorted(unique([ i.row() for i in self.parameterTableView.selectedIndexes() ])):
                param = self.currentMeasurement.parameters[index]
                self.measurementModel.addColumn( ('parameter',param.space.name,param.name) )
            self.updateComboBoxes()
                
    def updateComboBoxes(self):
        self.axisDict = dict( {"Started": ('measurement',None,'startDate') } )
        self.axisDict.update( dict( ((col[2], col) for col in self.measurementModel.extraColumns) ) )
        updateComboBoxItems(self.xComboBox, sorted(self.axisDict.keys()), self.settings.plotXAxis)
        updateComboBoxItems(self.yComboBox, sorted(self.axisDict.keys()), self.settings.plotYAxis)
        
    def onAddResultToMeasurement(self):
        if self.currentMeasurement is not None:
            for index in sorted(unique([ i.row() for i in self.resultTableView.selectedIndexes() ])):
                result = self.currentMeasurement.results[index]
                self.measurementModel.addColumn( ('result',None,result.name) )
            self.updateComboBoxes()
                        
    def onRemoveMeasurementColumn(self):
        for index in sorted(unique([ i.column() for i in self.measurementTableView.selectedIndexes() if i.column()>=self.measurementModel.coreColumnCount])):
            self.measurementModel.removeColumn(index)
            self.updateComboBoxes()
                        
    def onCommentFinished(self, document):
        if self.currentMeasurement is not None:
            self.currentMeasurement.longComment = str(document.toPlainText())
            self.plainTextEdit.setModified(False)
            self.currentMeasurement._sa_instance_state.session.commit()

    def setDateTimeEdit(self, attr, value):
        setattr( self.settings, attr, datetime(value) )

    def onChangeTimespan(self, index):
        self.settings.timespan = index
        isCustom = self.timespans[index] == 'Custom'
        self.toDateTimeEdit.setEnabled( isCustom )
        self.fromDateTimeEdit.setEnabled( isCustom )
        self.onFilterRefresh()

    def saveConfig(self):
        for splitter in self.mySplitters:
            self.config[self.configname+"."+splitter] = getattr(self, splitter).saveState()
        self.config[self.configname] = self.settings
        for tableView in self.myTableViews:
            self.config[self.configname+"."+tableView] = saveColumnWidth(getattr(self,tableView))
        
    def onActiveInstrumentChanged(self, modelIndex, modelIndex2 ):
        measurement = self.container.measurements[modelIndex.row()]
        self.parameterModel.setParameters( measurement.parameters )
        self.resultModel.setResults( measurement.results )
        self.plainTextEdit.setPlainText( firstNotNone( measurement.longComment, "" ) )
        self.currentMeasurement = measurement
        
    def onFilterRefresh(self):
        self.container.query( *self.fromToTimeLookup[self.settings.timespan](datetime.now()) )
        
    def onCreatePlot(self): 
        self.doCreatePlot( self.axisDict[self.settings.plotXAxis], self.axisDict[self.settings.plotYAxis], self.settings.plotWindow )
        self.cacheGarbageCollect()
        
    def onUpdatePlot(self):
        self.doCreatePlot( self.axisDict[self.settings.plotXAxis], self.axisDict[self.settings.plotYAxis], self.settings.plotWindow, update=True )
        self.cacheGarbageCollect()        
        
    def cacheGarbageCollect(self):
        for key, (ref,_) in self.cache.items():
            if ref() is None:
                self.cache.pop(key)
        
    def getParameter(self, measurement, space, name):
        param = measurement.parameterByName(space,name)
        return (param.value, None, None) if param is not None and not param.value.isinf() else None
        
    def getResult(self, measurement, space, name):
        result = measurement.resultByName(name)
        return (result.value, result.bottom, result.top) if result is not None and not result.value.isinf() else (None, None, None)

    def getData(self, xDataDef, yDataDef):
        xDataList = list()
        yDataList = list()
        bottomList = list()
        topList = list()
        xsource, xspace, xname = xDataDef
        ysource, yspace, yname = yDataDef
        for measurement in self.measurementModel.measurements:
            xData, _, _ = self.sourceLookup[xsource](measurement, xspace, xname)
            yData, bottom, top  = self.sourceLookup[ysource](measurement, yspace, yname)
            if xData is not None and yData is not None:
                xDataList.append( xData )
                yDataList.append( yData )
                if bottom is not None:
                    bottomList.append( bottom )
                if top is not None:
                    topList.append( top )
        if len(bottomList)==len(topList)==len(xDataList):
            return xDataList, yDataList, bottomList, topList
        return xDataList,yDataList, None, None
            
    def doCreatePlot(self, xDataDef, yDataDef, plotName, update=False ):
        ref, _ = self.cache.get( ( xDataDef, yDataDef ), (lambda: None, None)) 
        plottedTrace = ref() if update else None # get plottedtrace from the weakref if exists       
        # Assemble data
        xData, yData, bottomData, topData = self.getData(xDataDef, yDataDef)
        if len(xData)==0:
            logging.getLogger(__name__).error("Nothing to plot")
        else:
            if xDataDef==('measurement',None,'startDate'):
                epoch = datetime(1970, 1, 1) - timedelta(seconds=self.utcOffset) if xData[0].tzinfo is None else datetime(1970, 1, 1).replace(tzinfo=pytz.utc)
                time = numpy.array([(value - epoch).total_seconds() for value in xData])
                if plottedTrace is None:  # make a new plotted trace
                    trace = Trace(record_timestamps=False)
                    trace.name = "{0} versus {1}".format( yDataDef[2], xDataDef[2 ])
                    _, yUnit = yData[0].toval( returnUnit=True )
                    trace.y = numpy.array( [ d.toval(yUnit) for d in yData ] )
                    trace.x = time
                    if topData is not None and bottomData is not None:
                        trace.top = topData
                        trace.bottom = bottomData
                    traceui, item, view = self.plotWindowIndex[plotName]
                    plottedTrace = PlottedTrace( trace, view, xAxisLabel = "local time", windowName=item) 
                    plottedTrace.trace.filenameCallback = partial( WeakMethod.ref(plottedTrace.traceFilename), "" )
                    traceui.addTrace( plottedTrace, pen=-1)
                    traceui.resizeColumnsToContents()
                    self.cache[(xDataDef, yDataDef)] = ( weakref.ref(plottedTrace), (xDataDef, yDataDef, plotName) )
                else:  # update the existing plotted trace
                    trace = plottedTrace.trace
                    trace.y = yData
                    trace.x = time
                    trace.top = topData
                    trace.bottom = bottomData
                    plottedTrace.replot()     
            else:
                if plottedTrace is None:  # make a new plotted trace
                    trace = Trace(record_timestamps=False)
                    trace.name = "{0} versus {1}".format( yDataDef[2], xDataDef[2 ])
                    trace.y = yData
                    trace.x = xData
                    trace.top = topData
                    trace.bottom = bottomData
                    traceui, item, view = self.plotWindowIndex[plotName]
                    plottedTrace = PlottedTrace( trace, view, xAxisLabel = xDataDef[2], windowName=item) 
                    plottedTrace.trace.filenameCallback = partial( WeakMethod.ref(plottedTrace.traceFilename), "" )
                    traceui.addTrace( plottedTrace, pen=-1)
                    traceui.resizeColumnsToContents()
                    self.cache[(xDataDef, yDataDef)] = ( weakref.ref(plottedTrace), (xDataDef, yDataDef, plotName) )
                else:  # update the existing plotted trace
                    trace = plottedTrace.trace
                    trace.y = yData
                    trace.x = xData
                    trace.top = topData
                    trace.bottom = bottomData
                    plottedTrace.replot()     
                
    def onUpdateAll(self):
        for ref, context in self.cache.values():
            if ref() is not None:
                self.doCreatePlot(*context, update=True )
        self.cacheGarbageCollect()
            
        