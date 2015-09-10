"""
Created on 09 Sep 2015 at 2:26 PM

@author: jmizrahi
"""

import os.path
import sys
import yaml
from PyQt4 import QtGui, QtCore
import PyQt4.uic
ProjectConfigUiPath = os.path.join(os.path.dirname(__file__), '..', 'ui/ProjectConfig.ui')
ProjectConfigUiForm, ProjectConfigUiBase = PyQt4.uic.loadUiType(ProjectConfigUiPath)

class Project(object):
    def __init__(self):
        """initialize a project by loading in the project config information"""
        mainDir = os.path.join(os.path.dirname(__file__), '..') #main IonControl directory
        filename = 'config/ProjectConfig.yml' #relative path to config file
        self.projectConfigFilename = os.path.realpath(os.path.join(mainDir, filename)) #absolute path to config file

        #load in config information
        with open(self.projectConfigFilename, 'r') as f:
            self.__dict__.update(yaml.load(f))

        if not os.path.exists(self.baseDir): #If the baseDir doesn't exist, we have to use the GUI
            self.showProjectConfigGui = True
        elif not self.name: #If no project name is specified, we have to use the GUI
            self.showProjectConfigGui = True
        if self.showProjectConfigGui:
            ui = ProjectSelectionUi(self)
            ui.show()
            accept = ui.exec_()
            if not accept:
                sys.exit("Project must be selected for IonControl program to run")
            else: #overwrite the config file with the values just set
                with open(self.projectConfigFilename, 'w') as f:
                    yaml.dump({'showProjectConfigGui':self.showProjectConfigGui,
                               'baseDir':self.baseDir,
                               'name':self.name}, f, default_flow_style=False)

        self.projectDir = os.path.join(self.baseDir, self.name)
        if not os.path.exists(self.projectDir):
            os.makedirs(self.projectDir)

        #load in experiment configuration information
        self.exptConfigFilename = os.path.join(self.projectDir, 'ExptConfig.yml')
 #       if os.path.exists(self.exptConfigFilename):


class ProjectSelectionUi(ProjectConfigUiBase,ProjectConfigUiForm):
    """Class for selecting a project"""
    def __init__(self, project):
        ProjectConfigUiBase.__init__(self)
        ProjectConfigUiForm.__init__(self)
        self.project = project
        self.setupUi(self)

    def setupUi(self, parent):
        """setup the dialog box ui"""
        super(ProjectSelectionUi,self).setupUi(parent)
        self.infoLabel.setText(
            "This dialog box overwrites the configuration file {0}.".format(
                self.project.projectConfigFilename))
        self.setBaseDir()
        self.defaultCheckBox.setChecked(not self.project.showProjectConfigGui)
        self.populateProjectList()
        self.changeBaseDirectory.clicked.connect(self.onChangeBaseDirectory)
        self.createButton.clicked.connect(self.onCreate)

    def setBaseDir(self):
        """Get a valid base directory"""
        if not os.path.exists(self.project.baseDir):
            baseDir = str(QtGui.QFileDialog.getExistingDirectory(self,
                                                                 'Please select a base directory for projects',
                                                                 os.path.expanduser('~')
                                                                ))
            if not os.path.exists(baseDir):
                sys.exit("Valid base directory for projects must be specified for IonControl program to run")
            else:
                self.project.baseDir = baseDir
        self.baseDirectoryEdit.setText(self.project.baseDir)

    def onCreate(self):
        """Create a new project folder"""
        name = str(self.newProjectName.text())
        projectDir = os.path.join(self.project.baseDir, name)
        if not os.path.exists(projectDir):
            os.makedirs(projectDir)
        item = QtGui.QListWidgetItem(name)
        self.projectList.addItem(item)
        self.projectList.setCurrentItem(item)
        self.newProjectName.clear()

    def populateProjectList(self):
        self.projectList.clear()
        projects = [name for name in os.listdir(self.project.baseDir) if os.path.isdir(os.path.join(self.project.baseDir, name))]
        self.projectList.addItems(projects)
        matches = self.projectList.findItems(self.project.name, QtCore.Qt.MatchExactly)
        if matches:
            self.projectList.setCurrentItem(matches[0])
        elif projects:
            self.projectList.setCurrentRow(0)

    def onChangeBaseDirectory(self):
        baseDir = QtGui.QFileDialog.getExistingDirectory(self)
        if baseDir:
            self.project.baseDir = str(baseDir)
            self.baseDirectoryEdit.setText(baseDir)
            self.populateProjectList()

    def accept(self):
        selectedProject = self.projectList.currentItem()
        if selectedProject: #something is selected
            self.project.showProjectConfigGui = not self.defaultCheckBox.isChecked()
            self.project.name = str(selectedProject.text())
            ProjectConfigUiBase.accept(self)
        else: #if nothing is selected, equivalent to clicking cancel
            ProjectConfigUiBase.reject(self)

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    project = Project()


