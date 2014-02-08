# -*- coding: utf-8 -*-
"""
Created on Fri May 10 21:12:12 2013

@author: pmaunz
"""

import sys 

from PyQt4 import QtGui
import PyQt4.uic

import ProjectSelection


Form, Base = PyQt4.uic.loadUiType(r'ui\ProjectSelection.ui')

class ProjectSelectionUi(Form, Base):
    def __init__(self,parent=None):
        Base.__init__(self,parent)
        Form.__init__(self,parent)
        self.project = None
        self.defaultProject = ProjectSelection.defaultProject()
        
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
                index = self.projects.index(self.defaultProject)
                self.projectList.setCurrentRow( index )
            except ValueError:
                pass
        self.startupWidgets.setVisible( atProgramStart )
        self.warningLabel.setVisible( not atProgramStart)
            
    def onSetConfigFile(self):
        ProjectSelection.setSpecificConfigFile( str( self.configFileEdit.text()))
            
    def onOpenConfigFile(self): 
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open config file', gui.ProjectSelection.ProjectsBaseDir)
        gui.ProjectSelection.setSpecificConfigFile( str( fname ))
        self.configFileEdit.setText(fname)
                
    def onCreateProject(self):
        name = str(self.newProjectName.text())
        if name not in self.projects:
            gui.ProjectSelection.createProject(name)
            self.projects.append(name)
            self.projectList.addItem(name)
            
    def accept(self):
        if self.defaultCheckBox.isChecked():
            gui.ProjectSelection.setDefaultProject(str(self.projectList.currentItem().text()))
        else:
            gui.ProjectSelection.setDefaultProject(None)
        self.project = str(self.projectList.currentItem().text()) if self.projectList.currentItem() else None
        Base.accept(self)
        
def GetProjectSelection(atProgramStart=False):
    project = gui.ProjectSelection.defaultProject()
    if (not project) or (not atProgramStart):
        selectionui = ProjectSelectionUi()
        selectionui.setupUi(selectionui, atProgramStart)
        selectionui.exec_()
        project = selectionui.project
        gui.ProjectSelection.setProjectBaseDir( str(selectionui.baseDirectoryEdit.text()), atProgramStart)
    gui.ProjectSelection.setProject(project)
    return project, gui.ProjectSelection.projectDir()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    print GetProjectSelection(True)
    
    selectionui = ProjectSelectionUi()
    selectionui.setupUi(selectionui)
    selectionui.exec_()
    project = selectionui.project

