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
from persist.DatabaseConnectionSettings import DatabaseConectionSettings


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
                self.databaseConnectionLookup.setdefault( self.defaultProject, DatabaseConectionSettings())
            except ValueError:
                pass
        self.startupWidgets.setVisible( atProgramStart )
        self.warningLabel.setVisible( not atProgramStart)
        self.currentDatabaseConnection = self.databaseConnectionLookup.get(self.project, DatabaseConectionSettings())
        self.projectList.currentTextChanged.connect( self.onCurrentIndexChanged )
        self.userEdit.editingFinished.connect( partial( self.onStringValue, 'user', lambda: self.userEdit.text()))
        self.hostEdit.editingFinished.connect( partial( self.onStringValue, 'host', lambda: self.hostEdit.text()))
        self.databaseEdit.editingFinished.connect( partial( self.onStringValue, 'database', lambda: self.databaseEdit.text()))
        self.passwordEdit.editingFinished.connect( partial( self.onStringValue, 'password', lambda: self.passwordEdit.text()))
        self.portEdit.valueChanged.connect( self.onValueChanged )
        self.setDatabaseFields(self.currentDatabaseConnection)
           
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
            
    def accept(self):
        if self.defaultCheckBox.isChecked():
            ProjectSelection.setDefaultProject(str(self.projectList.currentItem().text()), self.databaseConnectionLookup)
        else:
            ProjectSelection.setDefaultProject(None, self.databaseConnectionLookup)
        self.project = str(self.projectList.currentItem().text()) if self.projectList.currentItem() else None
        Base.accept(self)
        
def GetProjectSelection(atProgramStart=False):
    project, dbConnectionLookup = ProjectSelection.defaultProject(returnDatabaseLookup=True)
    if (not project) or (not atProgramStart):
        selectionui = ProjectSelectionUi()
        selectionui.setupUi(selectionui, atProgramStart)
        selectionui.exec_()
        project = selectionui.project
        dbConnectionLookup = selectionui.databaseConnectionLookup
        ProjectSelection.setProjectBaseDir( str(selectionui.baseDirectoryEdit.text()), atProgramStart)
    ProjectSelection.setProject(project)
    return project, ProjectSelection.projectDir(), dbConnectionLookup.get(project, DatabaseConectionSettings())

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    print GetProjectSelection(True)
    
    selectionui = ProjectSelectionUi()
    selectionui.setupUi(selectionui)
    selectionui.exec_()
    project = selectionui.project

