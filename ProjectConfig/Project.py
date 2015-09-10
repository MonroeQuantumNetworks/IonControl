"""
Created on 09 Sep 2015 at 2:26 PM

@author: jmizrahi
"""

import __main__
import os.path
import sys
import yaml
import logging
from PyQt4 import QtGui, QtCore
import PyQt4.uic
from datetime import datetime
from persist.DatabaseConnectionSettings import DatabaseConnectionSettings
from ProjectConfigUi import ProjectConfigUi, projectTag
from ExptConfigUi import ExptConfigUi
from sqlalchemy import create_engine

uiPath = os.path.join(os.path.dirname(__file__), '..', 'ui/ProjectInfo.ui')
Form, Base = PyQt4.uic.loadUiType(uiPath)

projectName=None
projectDir=None
dbConnection=None

class Project(object):
    def __init__(self):
        """initialize a project by loading in the project config information"""
        logger = logging.getLogger(__name__)
        mainDir = os.path.join(os.path.dirname(__file__), '..') #main IonControl directory
        filename = 'config/ProjectConfig.yml' #relative path to config file
        self.projectConfig = {'baseDir':'', 'name':'', 'showGui':True} #default values
        self.exptConfig = {'showGui':True}
        self.projectConfigFilename = os.path.realpath(os.path.join(mainDir, filename)) #absolute path to config file

        #Load in the project config information
        if os.path.exists(self.projectConfigFilename):
            with open(self.projectConfigFilename, 'r') as f:
                try:
                    yamldata = yaml.load(f)
                    self.projectConfig = yamldata
                except yaml.scanner.ScannerError:
                    pass #leave defaults if the file is improperly formatted

        #If the baseDir doesn't exist or no project is specified, we have to use the GUI
        if not os.path.exists(self.projectConfig['baseDir']) or not self.projectConfig['name']:
            self.projectConfig['showGui'] = True

        if self.projectConfig['showGui']:
            ui = ProjectConfigUi(self)
            ui.show()
            ui.exec_()
            with open(self.projectConfigFilename, 'w') as f: #save information from GUI to file
                yaml.dump(self.projectConfig, f, default_flow_style=False)

        self.projectDir = os.path.join(self.projectConfig['baseDir'], self.projectConfig['name'])
        if not os.path.exists(self.projectDir):
            os.makedirs(self.projectDir)
            tagFilename = os.path.join(self.projectDir, projectTag)
            message = 'project {0} created {1}'.format(self.projectConfig['name'], datetime.now())
            with open(tagFilename, 'w') as f:
                f.write(message)
            logger.info(message)

        self.guiConfigDir = os.path.join(self.projectDir, '.gui-config')
        if not os.path.exists(self.guiConfigDir):
            os.makedirs(self.guiConfigDir)
        scriptname,_ = os.path.splitext( os.path.basename(__main__.__file__))
        self.guiConfigFile = os.path.join( self.guiConfigDir, scriptname+".config.db" )
        self.configDir = os.path.join(self.projectDir, 'config')
        if not os.path.exists(self.configDir):
            os.makedirs(self.configDir)

        #Load in the experiment config information
        self.exptConfigFilename = os.path.realpath(os.path.join(self.projectDir, 'config/ExptConfig.yml'))
        if os.path.exists(self.exptConfigFilename):
            with open(self.exptConfigFilename, 'r') as f:
                try:
                    yamldata = yaml.load(f)
                    self.exptConfig = yamldata
                except yaml.scanner.ScannerError:
                    pass #leave defaults if the file is improperly formatted

        if self.exptConfig.get('databaseConnection'):
            self.dbConnection = DatabaseConnectionSettings(**self.exptConfig['databaseConnection'])
            success = self.attemptDatabaseConnection()
            if not success:
                self.exptConfig['showGui']=True
                logger.info("Database connection failed - please check settings")

        if self.exptConfig['showGui']: #TODO: THIS DOESN'T WORK YET
            ui = ExptConfigUi(self)
            ui.show()
            ui.exec_()
            with open(self.exptConfigFilename, 'w') as f: #save information from GUI to file
                yaml.dump(self.exptConfig, f, default_flow_style=False)

        self.dbConnection = DatabaseConnectionSettings(**self.exptConfig['databaseConnection'])

        self.setGlobalProjectVars()

    @property
    def name(self):
        return self.projectConfig['name']

    def __str__(self):
        return self.name

    def setGlobalProjectVars(self):
        global projectDir
        global dbConnection
        global projectName
        projectName = self.name
        projectDir = self.projectDir
        dbConnection = self.dbConnection

    def attemptDatabaseConnection(self):
        """Attempt to connect to the database"""
        logger = logging.getLogger(__name__)
        try:
            engine = create_engine(self.dbConnection.connectionString, echo=self.dbConnection.echo)
            engine.connect()
            engine.dispose()
            success = True
            logger.info("Database connection successful")
        except Exception as e:
            success = False
        return success


class ProjectInfoUi(Base,Form):
    """Class for seeing project settings in the main GUI, and setting config GUIs to show on next program start"""
    def __init__(self, project):
        Base.__init__(self)
        Form.__init__(self)
        self.project = project
        self.setupUi(self)

    def setupUi(self, parent):
        """setup the dialog box ui"""
        super(ProjectInfoUi,self).setupUi(parent)
        self.ProjectConfigTextEdit.setText( yaml.dump(self.project.projectConfig, default_flow_style=False) )
        self.ExptConfigTextEdit.setText( yaml.dump(self.project.exptConfig, default_flow_style=False) )

    def accept(self):
        """update the config files based on the check boxes"""
        if self.showProjectGuiCheckbox.isChecked() and not self.project.projectConfig['showGui']:
            self.project.projectConfig.update({'showGui':True})
            with open(self.project.projectConfigFilename, 'w') as f:
                yaml.dump(self.project.projectConfig, f, default_flow_style=False)

        if self.showExptGuiCheckbox.isChecked() and not self.project.exptConfig['showGui']:
            self.project.exptConfig.update({'showGui':True})
            with open(self.project.exptConfigFilename, 'w') as f:
                yaml.dump(self.project.exptConfig, f, default_flow_style=False)

        Base.accept(self)


if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    project = Project()