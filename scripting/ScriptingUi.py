'''
Created on Jul 24, 2015

@author: jmizrahi
'''

import os.path

from PyQt4 import QtCore, QtGui
import PyQt4.uic
import logging
from PyQt4.Qsci import QsciScintilla
from datetime import datetime

from gui import ProjectSelection
from modules.PyqtUtility import BlockSignals
from modules import magnitude
from Script import Script, ScriptException, scriptFunctions
from pulseProgram.PulseProgramSourceEdit import PulseProgramSourceEdit

ScriptingWidget, ScriptingBase = PyQt4.uic.loadUiType('ui/Scripting.ui')

class ScriptingUi(ScriptingWidget,ScriptingBase):
    def __init__(self, config, globalVariablesUi):
        ScriptingWidget.__init__(self)
        ScriptingBase.__init__(self)
        self.config = config
        self.textEdit = None
        self.console = None
        self.recentFiles = dict() #dict of form {shortname: fullname}, where fullname has path and shortname doesn't
        self.globalVariablesUi = globalVariablesUi 
        self.script = Script() #encapsulates the script
        self.defaultDir = ProjectSelection.configDir()+'\\Scripts'
   
    def setupUi(self,parent):
        super(ScriptingUi,self).setupUi(parent)
        #logger = logging.getLogger(__name__)
        self.configname = 'Scripting'
        self.recentFiles = self.config.get( self.configname+'.recentFiles' , dict() )
        self.script.fullname = self.config.get( self.configname+'.script.fullname' , '' )
        self.script.shortname = os.path.basename(self.script.fullname)
        if self.script.fullname != '' and os.path.exists(self.script.fullname):
            with open(self.script.fullname,"r") as f:
                self.script.code = f.read()
        else:
            self.script.code = '' 
        self.script.locationSignal.connect( self.onLocation )
        self.script.finished.connect( self.onFinished )
        self.script.consoleSignal.connect(self.onConsoleSignal)
        self.script.setGlobalSignal.connect(self.onSetGlobal)
        self.script.addGlobalSignal.connect(self.onAddGlobal)

        self.textEdit = PulseProgramSourceEdit()
        self.textEdit.setupUi(self.textEdit,extraKeywords1=[], extraKeywords2=scriptFunctions)
        self.textEdit.textEdit.SendScintilla(QsciScintilla.SCI_SETCARETLINEVISIBLEALWAYS, True)
        self.textEdit.setPlainText(self.script.code)
        self.splitter.addWidget(self.textEdit)
        
        self.console = QtGui.QTextEdit()
        self.console.setReadOnly(True)
        self.splitter.addWidget(self.console)

        #Add only the filename (without the full path) to the combo box
        self.filenameComboBox.addItems( [shortname for shortname, fullname in self.recentFiles.iteritems() if os.path.exists(fullname)] )

        self.actionOpen.triggered.connect( self.onLoad )
        self.actionSave.triggered.connect( self.onSave )
        self.actionReset.triggered.connect(self.onReset)
        self.actionStart.triggered.connect( self.onStart )
        self.actionNew.triggered.connect( self.onNew )
        self.repeatButton.clicked.connect( self.onRepeat )
        
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
            try:
                func(self, *args, **kwds)
            except Exception as e:
                with QtCore.QMutexLocker(self.script.mutex):
                    self.script.exceptionOccurred = True
                    self.script.exception = e
            finally:
                self.script.waitCondition.wakeAll()
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
        logger = logging.getLogger(__name__)
        magValue = magnitude.mg(value, unit)
        doesNotExist = name not in self.globalVariablesUi.keys()
        if doesNotExist:
            self.globalVariablesUi.model.addVariable(name)
            message = "Global variable {0} created".format(name)
            logger.debug(message)
            self.writeToConsole(message, True)
        self.globalVariablesUi.model.update([('Global', name, magValue)])
        message = "Global variable {0} set to {1} {2}".format(name, value, unit)
        logger.debug(message)
        self.writeToConsole(message, True)
 
    @QtCore.pyqtSlot(str, float, str)
    @scriptCommand
    def onSetGlobal(self, name, value, unit):
        """Set global 'name' to 'value, unit'"""
        name = str(name) #signal is passed as a QString
        value = float(value)
        unit = str(unit)
        logger = logging.getLogger(__name__)
        magValue = magnitude.mg(value, unit)
        doesNotExist = (name not in self.globalVariablesUi.keys())
        if doesNotExist:
            message = "Global variable {0} does not exist.".format(name)
            logger.error(message)
            self.writeToConsole(message, False)
            raise ScriptException(message)
        self.globalVariablesUi.model.update([('Global', name, magValue)])
        message = "Global variable {0} set to {1} {2}".format(name, value, unit)
        logger.debug(message)
        self.writeToConsole(message, True)
        
    @QtCore.pyqtSlot(int)        
    def onLocation(self, currentLine):
        """Mark where the script currently is"""
        if currentLine >= 0:
            self.textEdit.textEdit.markerDeleteAll()
            self.textEdit.textEdit.markerAdd(currentLine-1, self.textEdit.textEdit.ARROW_MARKER_NUM)
            self.textEdit.textEdit.setCursorPosition(currentLine-1, 0)
        
    @QtCore.pyqtSlot()
    def onStart(self):
        """Starts the script and disables some aspects of the script GUI"""
        if not self.script.isRunning():
            self.statusLabel.setText("Script running")
            self.onSave()
            self.enableScriptChange(False)
            self.actionPause.setChecked(False)
            with QtCore.QMutexLocker(self.script.mutex):
                self.script.paused = False
                self.script.stopped = False
                self.script.exceptionOccurred = False
                self.script.exception = None
            self.script.start()
        
    def enableScriptChange(self, enabled):
        """Enable or disable any changes to script"""
        color = QtGui.QColor("#ffe4e4") if enabled else QtGui.QColor(0xd0, 0xff, 0xd0)
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
        self.statusLabel.setText("Idle")
        self.textEdit.textEdit.markerDeleteAll()
        self.enableScriptChange(True)
        
    @QtCore.pyqtSlot(str, bool)
    def onConsoleSignal(self, message, noError):
        self.writeToConsole(message, noError)
    
    def writeToConsole(self, message, noError):
        self.console.moveCursor(QtGui.QTextCursor.End)
        textColor = "black" if noError else "red"
        self.console.insertHtml(QtCore.QString('<font color='+textColor+'>'+message+'</font><br>'))

#     @QtCore.pyqtSlot(bool)
#     def onPause(self, paused):
#         print "paused = "+str(paused) 
#         self.script.mutex.lock()
#         self.script.paused = paused
#         self.script.mutex.unlock()
#         if not paused:
#             self.unPauseSignal.emit()
#         
#     @QtCore.pyqtSlot()
#     def pausedFromScript(self):
#         with QtCore.QMutexLocker(self.script.mutex):
#             self.actionPause.setChecked(self.script.paused)
#     
#     @QtCore.pyqtSlot()
#     def onStop(self):
#         self.script.mutex.lock()
#         self.script.stopped = True
#         self.script.mutex.unlock()
#         self.textEdit.textEdit.markerDeleteAll()
#         self.enableScriptChange(True)
#     
#     @QtCore.pyqtSlot()
#     def onStopImmediately(self):
#         self.script.terminate()
#         self.stopImmediatelySignal.emit()
#     
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
        with QtCore.QMutexLocker(self.script.mutex):
            self.script.repeat = self.repeatButton.isChecked()
             
    def onFilenameChange(self, shortname ):
        shortname = str(shortname)
        if shortname in self.recentFiles:
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
        self.hide()

