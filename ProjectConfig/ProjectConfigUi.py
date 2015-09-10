"""
Created on 10 Sep 2015 at 10:50 AM

@author: jmizrahi
"""
import os.path
import sys
import logging
from PyQt4 import QtGui, QtCore
import PyQt4.uic
from datetime import datetime

projectTag = '.IonControl-project.txt'

uiPath = os.path.join(os.path.dirname(__file__), '..', 'ui/ProjectConfig.ui')
Form, Base = PyQt4.uic.loadUiType(uiPath)

class ProjectConfigUi(Base,Form):
    """Class for selecting a project"""
    def __init__(self, project):
        Base.__init__(self)
        Form.__init__(self)
        self.project = project
        self.projectConfig = project.projectConfig
        self.setupUi(self)

    def setupUi(self, parent):
        """setup the dialog box ui"""
        super(ProjectConfigUi,self).setupUi(parent)
        self.infoLabel.setText(
            "This dialog box overwrites the configuration file {0}.".format(
                self.project.projectConfigFilename))
        self.setBaseDir()
        self.defaultCheckBox.setChecked(not self.projectConfig['showGui'])
        self.populateProjectList()
        self.changeBaseDirectory.clicked.connect(self.onChangeBaseDirectory)
        self.createButton.clicked.connect(self.onCreate)

    def setBaseDir(self):
        """Get a valid base directory"""
        logger = logging.getLogger(__name__)
        if not os.path.exists(self.projectConfig['baseDir']):
            baseDir = str(QtGui.QFileDialog.getExistingDirectory(self,
                                                                 'Please select a base directory for projects',
                                                                 os.path.expanduser('~')
                                                                ))
            if not os.path.exists(baseDir):
                message = "Valid base directory for projects must be specified for IonControl program to run"
                logger.exception(message)
                sys.exit(message)
            else:
                self.projectConfig['baseDir'] = baseDir
        self.baseDirectoryEdit.setText(self.projectConfig['baseDir'])

    def onCreate(self):
        """Create a new project folder"""
        name = str(self.newProjectName.text())
        projectDir = os.path.join(self.projectConfig['baseDir'], name)
        if not os.path.exists(projectDir):
            os.makedirs(projectDir)
            tagFilename = os.path.join(projectDir, projectTag)
            with open(tagFilename, 'w') as f:
                newFileText = 'project {0} created {1}'.format(name, datetime.now())
                f.write(newFileText)
        item = QtGui.QListWidgetItem(name)
        self.projectList.addItem(item)
        self.projectList.setCurrentItem(item)
        self.newProjectName.clear()

    def populateProjectList(self):
        self.projectList.clear()
        projects = [name for name in os.listdir(self.projectConfig['baseDir']) if os.path.exists(os.path.join(self.projectConfig['baseDir'], name, projectTag))]
        self.projectList.addItems(projects)
        matches = self.projectList.findItems(self.projectConfig['name'], QtCore.Qt.MatchExactly)
        if matches:
            self.projectList.setCurrentItem(matches[0])
        elif projects:
            self.projectList.setCurrentRow(0)

    def onChangeBaseDirectory(self):
        baseDir = QtGui.QFileDialog.getExistingDirectory(self)
        if baseDir:
            self.projectConfig['baseDir'] = str(baseDir)
            self.baseDirectoryEdit.setText(baseDir)
            self.populateProjectList()

    def accept(self):
        selectedProject = self.projectList.currentItem()
        if selectedProject: #something is selected
            self.projectConfig['showGui'] = not self.defaultCheckBox.isChecked()
            self.projectConfig['name'] = str(selectedProject.text())
            Base.accept(self)
        else: #if nothing is selected, equivalent to clicking cancel
            Base.reject(self)

    def reject(self):
        message = "Project must be selected for IonControl program to run"
        logging.getLogger(__name__).exception(message)
        sys.exit(message)
