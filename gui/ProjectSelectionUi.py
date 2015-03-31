# -*- coding: utf-8 -*-
"""
Created on Fri May 10 21:12:12 2013

@author: pmaunz
"""

import sys 

from PyQt4 import QtGui, QtCore
import PyQt4.uic

import ProjectSelection
from _functools import partial
from persist.DatabaseConnectionSettings import DatabaseConnectionSettings


Form, Base = PyQt4.uic.loadUiType(r'ui\ProjectSelection.ui')

class ProjectSelectionUi(Form, Base):
    def __init__(self,parent=None):
        Base.__init__(self,parent)
        Form.__init__(self,parent)
        self.project = None
        self.defaultProject, self.databaseConnectionLookup = ProjectSelection.defaultProject(returnDatabaseLookup=True)
        
    def setupUi(self,parent, atProgramStart):
        Form.setupUi(self,parent)
        self.projects = ProjectSelection.projects()
        self.projectList.addItems( self.projects )
        self.projectList.doubleClicked.connect( self.onDoubleClicked )
        self.project = ProjectSelection.lastProject()
        if self.project:
            found = self.projectList.findItems( self.project, QtCore.Qt.MatchExactly )
            if found:
                self.projectList.setCurrentItem(found[0])
        self.createButton.clicked.connect( self.onCreateProject )
        self.defaultCheckBox.setChecked( bool(self.defaultProject) )
        self.baseDirectoryEdit.setText( ProjectSelection.ProjectsBaseDir )
        self.configFileToolButton.clicked.connect( self.onOpenConfigFile )
        self.configFileEdit.editingFinished.connect( self.onSetConfigFile )
        if self.defaultProject:
            try:
                self.project = self.defaultProject
                index = self.projects.index(self.defaultProject)
                self.projectList.setCurrentRow( index )
                self.databaseConnectionLookup.setdefault( self.defaultProject, DatabaseConnectionSettings())
            except ValueError:
                pass
        self.startupWidgets.setVisible( atProgramStart )
        self.warningLabel.setVisible( not atProgramStart)
        self.currentDatabaseConnection = self.databaseConnectionLookup.get(self.project, DatabaseConnectionSettings())
        self.projectList.currentTextChanged.connect( self.onCurrentIndexChanged )
        self.userEdit.editingFinished.connect( partial( self.onStringValue, 'user', lambda: self.userEdit.text()))
        self.hostEdit.editingFinished.connect( partial( self.onStringValue, 'host', lambda: self.hostEdit.text()))
        self.databaseEdit.editingFinished.connect( partial( self.onStringValue, 'database', lambda: self.databaseEdit.text()))
        self.passwordEdit.editingFinished.connect( partial( self.onStringValue, 'password', lambda: self.passwordEdit.text()))
        self.echoCheck.stateChanged.connect( self.onStateChanged )
        self.portEdit.valueChanged.connect( self.onValueChanged )
        self.setDatabaseFields(self.currentDatabaseConnection)
           
    def onStateChanged(self, value):
        self.currentDatabaseConnection.echo = value==QtCore.Qt.Checked
           
    def onValueChanged(self, value):
        self.currentDatabaseConnection.port = value
           
    def onStringValue(self, attr, value):
        setattr( self.currentDatabaseConnection, attr, str(value()))
           
    def onCurrentIndexChanged(self, value):
        self.databaseConnectionLookup[self.project] = self.currentDatabaseConnection
        self.project = str(value)
        self.databaseConnectionLookup.setdefault(self.project, self.currentDatabaseConnection)
        self.currentDatabaseConnection = self.databaseConnectionLookup.get( self.project )
        self.setDatabaseFields(self.currentDatabaseConnection)
        
    def setDatabaseFields(self, databaseConnect):
        self.userEdit.setText( databaseConnect.user )
        self.hostEdit.setText( databaseConnect.host )
        self.databaseEdit.setText( databaseConnect.database )
        self.passwordEdit.setText( databaseConnect.password )
        self.portEdit.setValue( databaseConnect.port )
        
            
    def onSetConfigFile(self):
        ProjectSelection.setSpecificConfigFile( str( self.configFileEdit.text()))
            
    def onOpenConfigFile(self): 
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open config file', ProjectSelection.ProjectsBaseDir)
        ProjectSelection.setSpecificConfigFile( str( fname ))
        self.configFileEdit.setText(fname)
                
    def onCreateProject(self):
        name = str(self.newProjectName.text())
        if name not in self.projects:
            ProjectSelection.createProject(name)
            self.projects.append(name)
            self.projectList.addItem(name)
            
    def onDoubleClicked(self, index):
        self.accept()
            
    def accept(self):
        if self.defaultCheckBox.isChecked():
            ProjectSelection.setDefaultProject(str(self.projectList.currentItem().text()), lastProject=str(self.projectList.currentItem().text()), 
                                               databaseConnectionLookup=self.databaseConnectionLookup)
        else:
            ProjectSelection.setDefaultProject(None, lastProject=str(self.projectList.currentItem().text()), 
                                               databaseConnectionLookup=self.databaseConnectionLookup)
        self.project = str(self.projectList.currentItem().text()) if self.projectList.currentItem() else None
        Base.accept(self)
        
def GetProjectSelection(atProgramStart=False):
    accepted = True
    project, dbConnectionLookup = ProjectSelection.defaultProject(returnDatabaseLookup=True)
    if (not project) or (not atProgramStart) or (not dbConnectionLookup):
        selectionui = ProjectSelectionUi()
        selectionui.setupUi(selectionui, atProgramStart)
        accepted = bool(selectionui.exec_())
        project = selectionui.project
        dbConnectionLookup = selectionui.databaseConnectionLookup
        ProjectSelection.setProjectBaseDir( str(selectionui.baseDirectoryEdit.text()), atProgramStart)
    ProjectSelection.setProject(project)
    return project, ProjectSelection.projectDir(), dbConnectionLookup.get(project, DatabaseConnectionSettings()), accepted

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    print GetProjectSelection(True)
    
    selectionui = ProjectSelectionUi()
    selectionui.setupUi(selectionui)
    selectionui.exec_()
    project = selectionui.project

