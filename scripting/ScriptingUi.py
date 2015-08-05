'''
Created on Jul 24, 2015

@author: jmizrahi
'''

import os.path

from PyQt4 import QtCore, QtGui
import PyQt4.uic
from PyQt4.Qsci import QsciScintilla
from PyQt4.QtCore import Qt
import logging
from datetime import datetime
from gui import ProjectSelection
from modules.PyqtUtility import BlockSignals
from modules import magnitude
from Script import Script, ScriptException, scriptFunctions, scriptFunctionDocs
from pulseProgram.PulseProgramSourceEdit import PulseProgramSourceEdit
import traceback

ScriptingWidget, ScriptingBase = PyQt4.uic.loadUiType('ui/Scripting.ui')

class ScriptingUi(ScriptingWidget,ScriptingBase):
    def __init__(self, experimentUi):
        ScriptingWidget.__init__(self)
        ScriptingBase.__init__(self)
        self.experimentUi = experimentUi
        self.config = experimentUi.config
        self.recentFiles = dict() #dict of form {shortname: fullname}, where fullname has path and shortname doesn't
        self.script = Script() #encapsulates the script
        self.defaultDir = ProjectSelection.configDir()+'\\Scripts'
   
    def setupUi(self,parent):
        super(ScriptingUi,self).setupUi(parent)
        #logger = logging.getLogger(__name__)
        self.configname = 'Scripting'
        
        #setup console
        self.consoleMaximumLines = self.config.get(self.configname+'.consoleMaximumLinesNew',100)
        self.consoleEnable = self.config.get(self.configname+'.consoleEnable',False)
        self.consoleClearButton.clicked.connect( self.onClearConsole )
        self.linesSpinBox.valueChanged.connect( self.onConsoleMaximumLinesChanged )
        self.linesSpinBox.setValue( self.consoleMaximumLines )
        self.checkBoxEnableConsole.stateChanged.connect( self.onEnableConsole )
        self.checkBoxEnableConsole.setChecked( self.consoleEnable )
        
        self.recentFiles = self.config.get( self.configname+'.recentFiles' , dict() )
        self.script.fullname = self.config.get( self.configname+'.script.fullname' , '' )
        self.script.shortname = os.path.basename(self.script.fullname)
        if self.script.fullname != '' and os.path.exists(self.script.fullname):
            with open(self.script.fullname,"r") as f:
                self.script.code = f.read()
        else:
            self.script.code = '' 
            
        self.script.locationSignal.connect( self.onLocation )
        self.script.exceptionSignal.connect( self.onException )
        self.script.finished.connect( self.onFinished )
        self.script.consoleSignal.connect(self.onConsoleSignal)

        self.script.setGlobalSignal.connect(self.onSetGlobal)
        self.script.addGlobalSignal.connect(self.onAddGlobal)
        self.script.pauseScriptSignal.connect(self.onPauseScriptFromScript)
        self.script.stopScriptSignal.connect(self.onStopScriptFromScript)
        self.script.startScanSignal.connect(self.onStartScan)
        self.script.setScanSignal.connect(self.onSetScan)
        self.script.setEvaluationSignal.connect(self.onSetEvaluation)
        self.script.setAnalysisSignal.connect(self.onSetAnalysis)
        self.script.plotPointSignal.connect(self.onPlotPoint)
        self.script.addPlotSignal.connect(self.onAddPlot)
        self.script.pauseScanSignal.connect(self.onPauseScan)
        self.script.stopScanSignal.connect(self.onStopScan)
        self.script.abortScanSignal.connect(self.onAbortScan)
        self.script.helpSignal.connect(self.onHelp)

        self.textEdit = PulseProgramSourceEdit()
        self.textEdit.setupUi(self.textEdit,extraKeywords1=[], extraKeywords2=scriptFunctions)
        self.textEdit.textEdit.currentLineMarkerNum = 9
        self.textEdit.textEdit.markerDefine(QsciScintilla.Background, self.textEdit.textEdit.currentLineMarkerNum)
        self.textEdit.textEdit.setMarkerBackgroundColor(QtGui.QColor(0xd0, 0xff, 0xd0), self.textEdit.textEdit.currentLineMarkerNum)
        
        self.textEdit.setPlainText(self.script.code)
        self.splitter.insertWidget(0,self.textEdit)
        
        #Add only the filename (without the full path) to the combo box
        self.filenameComboBox.addItems( [shortname for shortname, fullname in self.recentFiles.iteritems() if os.path.exists(fullname)] )

        self.repeatButton.clicked.connect( self.onRepeat )
        self.slowButton.clicked.connect( self.onSlow )
        #File control actions
        self.actionOpen.triggered.connect( self.onLoad )
        self.actionSave.triggered.connect( self.onSave )
        self.actionReset.triggered.connect(self.onReset)
        self.actionNew.triggered.connect( self.onNew )
        #Script control actions
        self.actionStartScript.triggered.connect( self.onStartScript )
        self.actionPauseScript.triggered.connect( self.onPauseScript )
        self.actionStopScript.triggered.connect( self.onStopScript )
        self.actionPauseScriptAndScan.triggered.connect( self.onPauseScriptAndScan )
        self.actionStopScriptAndScan.triggered.connect( self.onStopScriptAndScan )
        self.terminateButton.clicked.connect( self.onTerminate )
        
        self.filenameComboBox.currentIndexChanged[str].connect( self.onFilenameChange )
        self.removeCurrent.clicked.connect( self.onRemoveCurrent )
        
        self.loadFile(self.script.fullname)
        
        self.setWindowTitle(self.configname)
        self.setWindowIcon(QtGui.QIcon(":/other/icons/Terminal-icon.png"))
        self.statusLabel.setText("Idle")
    
    def scriptCommand(func):#@NoSelf
        """Decorator for script commands. 
        
        Catches exceptions, sets the script exception variables, and wakes the script after the
        specified action has been completed.
        """
        def baseScriptCommand(self, *args, **kwds):
            logger = logging.getLogger(__name__)
            try:
                message = func(self, *args, **kwds)
                if message:
                    logger.debug(message)
                    self.writeToConsole(message)
            except Exception as e:
                with QtCore.QMutexLocker(self.script.mutex):
                    self.script.exception = e
                    print traceback.print_exc()
            finally:
                self.script.commandWait.wakeAll()
        baseScriptCommand.func_name = func.func_name
        baseScriptCommand.func_doc = func.func_doc
        return baseScriptCommand
     
    @QtCore.pyqtSlot(str, float, str)
    @scriptCommand
    def onAddGlobal(self, name, value, unit):
        """Add a global 'name' and set it to 'value, unit'"""
        name = str(name) #signal is passed as a QString
        value = float(value)
        unit = str(unit)
        magValue = magnitude.mg(value, unit)
        doesNotExist = name not in self.experimentUi.globalVariablesUi.keys()
        message1 = ''
        if doesNotExist:
            self.experimentUi.globalVariablesUi.model.addVariable(name)
            message1 = "Global variable {0} created\n".format(name)
        self.experimentUi.globalVariablesUi.model.update([('Global', name, magValue)])
        message2 =  "Global variable {0} set to {1} {2}".format(name, value, unit)
        return message1+message2
 
    @QtCore.pyqtSlot(str, float, str)
    @scriptCommand
    def onSetGlobal(self, name, value, unit):
        """Set global 'name' to 'value, unit'"""
        name = str(name) #signal is passed as a QString
        value = float(value)
        unit = str(unit)
        logger = logging.getLogger(__name__)
        magValue = magnitude.mg(value, unit)
        doesNotExist = (name not in self.experimentUi.globalVariablesUi.keys())
        if doesNotExist:
            message = "Global variable {0} does not exist.".format(name)
            logger.error(message)
            self.writeToConsole(message, noError=False)
            raise ScriptException(message)
        self.experimentUi.globalVariablesUi.model.update([('Global', name, magValue)])
        return "Global variable {0} set to {1} {2}".format(name, value, unit)
    
    @QtCore.pyqtSlot()
    @scriptCommand
    def onStartScan(self):
        """Start the scan"""
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.scanRunning = True
        self.experimentUi.actionStart.trigger()
#        return "Scan started with scan = {0}, evaluation = {1}".format()

    @QtCore.pyqtSlot()
    @scriptCommand
    def onPauseScan(self):
        self.experimentUi.actionPause.trigger()
        return "Scan paused"
        
    @QtCore.pyqtSlot()
    @scriptCommand
    def onStopScan(self):
        self.experimentUi.actionStop.trigger()
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.scanRunning = False
        return "Scan stopped"
        
    @QtCore.pyqtSlot()
    @scriptCommand
    def onAbortScan(self):
        self.experimentUi.actionAbort.trigger()
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.scanRunning = False
        return "Scan aborted"

    @QtCore.pyqtSlot(str)
    @scriptCommand
    def onSetScan(self, name):
        pass
    
    @QtCore.pyqtSlot(str)
    @scriptCommand
    def onSetEvaluation(self, name):
        pass
    
    @QtCore.pyqtSlot(str)
    @scriptCommand
    def onSetAnalysis(self, name):
        pass
    
    @QtCore.pyqtSlot(float, float, str, str, bool)
    @scriptCommand
    def onPlotPoint(self, x, y, plotName, traceName, save):
        pass
    
    @QtCore.pyqtSlot(str)
    @scriptCommand
    def onAddPlot(self, name):
        pass
    
    @QtCore.pyqtSlot()
    @scriptCommand
    def onPauseScriptFromScript(self):
        self.onPauseScript(True)
        return 'script paused'

    @QtCore.pyqtSlot()
    @scriptCommand
    def onStopScriptFromScript(self):
        self.onStopScript()
        return 'script stopped'        
    
    @QtCore.pyqtSlot()
    @scriptCommand
    def onHelp(self):
        for _, doc in scriptFunctionDocs.iteritems():
            for n, line in enumerate(doc.splitlines()):
                self.writeToConsole(line, color='blue')
            self.writeToConsole('====================')
        
    @QtCore.pyqtSlot(list)        
    def onLocation(self, currentLines):
        """Mark where the script currently is"""
        if currentLines != []:
            self.textEdit.textEdit.markerDeleteAll()
            for line in currentLines:
                self.textEdit.textEdit.markerAdd(line-1, self.textEdit.textEdit.ARROW_MARKER_NUM)
                self.textEdit.textEdit.markerAdd(line-1, self.textEdit.textEdit.currentLineMarkerNum)
                
    @QtCore.pyqtSlot()
    def onStartScript(self):
        """Runs when start button clicked. Starts the script and disables some aspects of the script GUI"""
        if not self.script.isRunning():
            logger = logging.getLogger(__name__)
            self.statusLabel.setText("Script running")
            message = "script {0} started at {1}".format(self.script.fullname, str(datetime.now()))
            logger.debug(message)
            self.writeToConsole(message, color='blue')
            self.onSave()
            self.enableScriptChange(False)
            self.actionPauseScript.setChecked(False)
            with QtCore.QMutexLocker(self.script.mutex):
                self.script.paused = False
                self.script.stopped = False
                self.script.exceptionLine = -1
                self.script.exception = None
            self.script.start()
            
    @QtCore.pyqtSlot(bool)
    def onPauseScript(self, paused):
        logger = logging.getLogger(__name__)
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.paused = paused
            self.actionPauseScript.setChecked(paused)
            if not paused:
                self.script.pauseWait.wakeAll()
        message = "Script is paused" if paused else "Script is unpaused"
        logger.debug(message)
        self.writeToConsole(message, color='blue')

    @QtCore.pyqtSlot()
    def onStopScript(self):
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.stopped = True
            self.script.paused = False
            self.script.repeat = False
            self.actionPauseScript.setChecked(False)
            self.repeatButton.setChecked(False)
            self.script.commandWait.wakeAll()
            self.script.pauseWait.wakeAll()
            self.script.scanWait.wakeAll()
            self.script.dataWait.wakeAll()
        
    @QtCore.pyqtSlot()
    def onPauseScriptAndScan(self):
        self.onPauseScript(True)
        self.experimentUi.actionPause.trigger()
        
    @QtCore.pyqtSlot()
    def onStopScriptAndScan(self):
        self.onStopScript()
        self.experimentUi.actionStop.trigger()
        
    @QtCore.pyqtSlot()
    def onTerminate(self):
        warningResponse = self.warningMessage("Are you sure you want to terminate the script?", "This is probably a bad idea.")        
        if warningResponse == QtGui.QMessageBox.Ok:
            self.script.terminate()
 
    def warningMessage(self, warningText, informativeText):
        """Pop up a warning message. Return the response."""
        warningMessage = QtGui.QMessageBox()
        warningMessage.setText(warningText)
        warningMessage.setInformativeText(informativeText)
        warningMessage.setStandardButtons(QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
        return warningMessage.exec_() 

    def enableScriptChange(self, enabled):
        """Enable or disable any changes to script"""
        color = QtGui.QColor("#ffe4e4") if enabled else QtGui.QColor('white')
        width = 1 if enabled else 0
        self.textEdit.textEdit.setCaretWidth(width)
        self.textEdit.textEdit.setCaretLineBackgroundColor(color)
        self.textEdit.setDisabled(not enabled)
        self.filenameComboBox.setDisabled(not enabled)
        self.removeCurrent.setDisabled(not enabled)
        self.actionOpen.setEnabled(enabled)
        self.actionSave.setEnabled(enabled)
        self.actionReset.setEnabled(enabled)
        self.actionNew.setEnabled(enabled)
    
    @QtCore.pyqtSlot()
    def onFinished(self):
        """Runs when script thread finishes. re-enables script GUI."""
        logger = logging.getLogger(__name__)
        self.statusLabel.setText("Idle")
        message = "script {0} finished at {1}".format(self.script.fullname, str(datetime.now()))
        logger.debug(message)
        self.writeToConsole(message, color='blue')
        self.textEdit.textEdit.markerDeleteAll()
        self.enableScriptChange(True)
        
    @QtCore.pyqtSlot(str, bool, str)
    def onConsoleSignal(self, message, noError, color):
        self.writeToConsole(message, noError=noError, color=color)
    
    @QtCore.pyqtSlot(int, str)
    def onException(self, currentLines, message):
        if currentLines != []:
            for line in currentLines:
                self.textEdit.highlightError(message, line)
    
    @QtCore.pyqtSlot()
    def onNew(self):
        logger = logging.getLogger(__name__)
        shortname, ok = QtGui.QInputDialog.getText(self, 'New script name', 'Please enter a new script name: ')
        if ok:
            shortname = str(shortname)
            shortname = shortname.replace(' ', '_') #Replace spaces with underscores
            shortname = shortname.split('.')[0] + '.py' #Take only what's before the '.', and add the .py extension
            fullname = self.defaultDir + '\\' + shortname
            if not os.path.exists(fullname):
                try:
                    with open(fullname, 'w') as f:
                        newFileText = '#' + shortname + ' created ' + str(datetime.now()) + '\n'
                        f.write(newFileText)
                except Exception as e:
                    message = "Unable to create new file {0}: {1}".format(shortname, e)
                    logger.error(message)
                    self.onConsoleSignal(message, False)
                    return
            self.loadFile(fullname)
            
    @QtCore.pyqtSlot()
    def onRepeat(self):
        logger = logging.getLogger(__name__)
        with QtCore.QMutexLocker(self.script.mutex):
            repeat = self.repeatButton.isChecked()
            self.script.repeat = repeat
            message = "Repeat is on" if repeat else "Repeat is off"
            logger.debug(message)
            self.writeToConsole(message)

    @QtCore.pyqtSlot()
    def onSlow(self):
        logger = logging.getLogger(__name__)
        with QtCore.QMutexLocker(self.script.mutex):
            slow = self.slowButton.isChecked()
            self.script.slow = slow
            message = "Slow is on" if slow else "Slow is off"
            logger.debug(message)
            self.writeToConsole(message)
             
    def onFilenameChange(self, shortname ):
        shortname = str(shortname)
        logger = logging.getLogger(__name__)
        if shortname not in self.recentFiles:
            logger.info('Use "open" or "new" commands to access a file not in the drop down menu')
            self.loadFile(self.recentFiles[self.script.shortname])
        else:
            fullname = self.recentFiles[shortname]
            if os.path.isfile(fullname) and fullname != self.script.fullname:
                self.loadFile(fullname)
                if str(self.filenameComboBox.currentText())!=fullname:
                    with BlockSignals(self.filenameComboBox) as w:
                        w.setCurrentIndex( self.filenameComboBox.findText( shortname ))
    
    def onLoad(self):
        fullname = str(QtGui.QFileDialog.getOpenFileName(self, 'Open Scripting file',self.defaultDir,'Python scripts (*.py *.pyw)'))
        if fullname!="":
            self.loadFile(fullname)
           
    def loadFile(self, fullname):
        logger = logging.getLogger(__name__)
        if fullname:
            self.script.fullname = fullname
            self.script.shortname = os.path.basename(fullname) 
            with open(fullname,"r") as f:
                self.script.code = f.read()
            self.textEdit.setPlainText(self.script.code)
            if self.script.shortname not in self.recentFiles:
                self.filenameComboBox.addItem(self.script.shortname)
            self.recentFiles[self.script.shortname] = fullname
            with BlockSignals(self.filenameComboBox) as w:
                w.setCurrentIndex( self.filenameComboBox.findText(self.script.shortname))
            logger.info('{0} loaded'.format(self.script.fullname))
            
    def onReset(self):
        if self.script.fullname:
            self.loadFile(self.script.fullname)

    def onRemoveCurrent(self):
        text = str(self.filenameComboBox.currentText())
        if text in self.recentFiles:
            self.recentFiles.pop(text)
        self.filenameComboBox.removeItem(self.filenameComboBox.currentIndex())

    def onSave(self):
        logger = logging.getLogger(__name__)
        self.script.code = str(self.textEdit.toPlainText())
        self.textEdit.clearHighlightError()
        if self.script.code and self.script.fullname:
            with open(self.script.fullname, 'w') as f:
                f.write(self.script.code)
                logger.info('{0} saved'.format(self.script.fullname))
    
    def saveConfig(self):
        self.config[self.configname+'.recentFiles'] = self.recentFiles
        self.config[self.configname+'.script.fullname'] = self.script.fullname
       
    def show(self):
        pos = self.config.get(self.configname+'.ScriptingUi.pos')
        size = self.config.get(self.configname+'.ScriptingUi.size')
        if pos:
            self.move(pos)
        if size:
            self.resize(size)
        QtGui.QDialog.show(self)
        self.isShown = True

    def onClose(self):
        self.config[self.configname+'.ScriptingUi.pos'] = self.pos()
        self.config[self.configname+'.ScriptingUi.size'] = self.size()
        self.config[self.configname+'.consoleMaximumLinesNew'] = self.consoleMaximumLines
        self.config[self.configname+'.consoleEnable'] = self.consoleEnable 
        self.hide()
    def onClearConsole(self):
        self.textEditConsole.clear()

    def onConsoleMaximumLinesChanged(self, maxlines):
        self.consoleMaximumLines = maxlines
        self.textEditConsole.document().setMaximumBlockCount(maxlines)

    def onEnableConsole(self, state):
        self.consoleEnable = state==QtCore.Qt.Checked

    def writeToConsole(self, message, noError=True, color=''):
        if self.consoleEnable:
            message = str(message)
            cursor = self.textEditConsole.textCursor()
            self.textEditConsole.moveCursor(QtGui.QTextCursor.End)
            textColor = ('black' if noError else 'red') if color=='' else color
            self.textEditConsole.setUpdatesEnabled(False)
            for line in message.splitlines():
                if textColor == 'black':
                    self.textEditConsole.insertPlainText(line+'\n')
                else:
                    self.textEditConsole.insertHtml(QtCore.QString('<p><font color='+textColor+'>'+line+'</font><br></p>'))
            self.textEditConsole.setUpdatesEnabled(True)
            self.textEditConsole.ensureCursorVisible()
