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
from ProjectConfigUi import ProjectConfigUi
from ExptConfigUi import ExptConfigUi
from sqlalchemy import create_engine

uiPath = os.path.join(os.path.dirname(__file__), '..', 'ui/ProjectInfo.ui')
Form, Base = PyQt4.uic.loadUiType(uiPath)

currentProject=None


class Project(object):
    def __init__(self):
        """initialize a project by loading in the project config information"""
        logger = logging.getLogger(__name__)
        self.mainConfigDir = os.path.realpath(os.path.join(os.path.dirname(__file__), '..', 'config')) #IonControl/config directory
        filename = 'ProjectConfig.yml'
        self.projectConfigFilename = os.path.realpath(os.path.join(self.mainConfigDir, filename)) #absolute path to config file
        self.projectConfig = {'baseDir':'', 'name':'', 'showGui':True} #default values
        self.exptConfig = {'hardware':dict(),'software':dict(),'databaseConnection':dict(),'showGui':True} #default values

        #Load in the project config information
        if os.path.exists(self.projectConfigFilename):
            with open(self.projectConfigFilename, 'r') as f:
                try:
                    yamldata = yaml.load(f)
                    self.projectConfig = yamldata
                    logger.info('Project config file {0} loaded'.format(self.projectConfigFilename))
                except yaml.scanner.ScannerError: #leave defaults if the file is improperly formatted
                    logger.warning('YAML formatting error: unable to read in project config file {0}'.format(self.projectConfigFilename))

        #If the baseDir doesn't exist or no project is specified, we have to use the GUI
        if not os.path.exists(self.projectConfig['baseDir']) or not self.projectConfig['name']:
            self.projectConfig['showGui'] = True

        if self.projectConfig['showGui']:
            ui = ProjectConfigUi(self)
            ui.show()
            ui.exec_()
            with open(self.projectConfigFilename, 'w') as f: #save information from GUI to file
                yaml.dump(self.projectConfig, f, default_flow_style=False)
                logger.info('GUI data saved to {0}'.format(self.projectConfigFilename))

        #make project directories if they don't exist
        self.projectDir = os.path.join(self.projectConfig['baseDir'], self.projectConfig['name'])
        self.configDir = os.path.join(self.projectDir,'config')
        self.guiConfigDir = os.path.join(self.projectDir, '.gui-config')
        scriptname,_ = os.path.splitext( os.path.basename(__main__.__file__) )
        self.guiConfigFile = os.path.join( self.guiConfigDir, scriptname+".config.db" )
        self.exptConfigFilename = os.path.realpath(os.path.join(self.configDir, 'ExptConfig.yml'))

        if not os.path.exists(self.projectDir):
            os.makedirs(self.projectDir)
            logger.debug('Directory {0} created'.format(self.projectDir))

        if not os.path.exists(self.configDir):
            os.makedirs(self.configDir)
            logger.debug('Directory {0} created'.format(self.configDir))
            with open(self.exptConfigFilename, 'w') as f:
                yaml.dump(self.exptConfig, f, default_flow_style=False)
                logger.debug('File {0} created'.format(self.exptConfigFilename))

        if not os.path.exists(self.guiConfigDir):
            os.makedirs(self.guiConfigDir)

        #Load in the experiment config information
        if os.path.exists(self.exptConfigFilename):
            with open(self.exptConfigFilename, 'r') as f:
                try:
                    yamldata = yaml.load(f)
                    self.exptConfig = yamldata
                    logger.info('Experiment config file {0} loaded'.format(self.exptConfigFilename))
                except yaml.scanner.ScannerError: #leave defaults if the file is improperly formatted
                    logger.warning('YAML formatting error: unable to read in experiment config file {0}'.format(self.exptConfigFilename))

        if self.exptConfig.get('databaseConnection') and not self.exptConfig.get('showGui'):
            self.dbConnection = DatabaseConnectionSettings(**self.exptConfig['databaseConnection'])
            success = self.attemptDatabaseConnection(self.dbConnection)
            if not success:
                self.exptConfig['showGui']=True

        if self.exptConfig['showGui']:
            ui = ExptConfigUi(self)
            ui.show()
            ui.exec_()
            self.exptConfig = ui.exptConfig
            with open(self.exptConfigFilename, 'w') as f: #save information from GUI to file
                yaml.dump(self.exptConfig, f, default_flow_style=False)
                logger.info('GUI data saved to {0}'.format(self.exptConfigFilename))

        self.dbConnection = DatabaseConnectionSettings(**self.exptConfig['databaseConnection'])

        self.setGlobalProject()

    @property
    def name(self):
        return self.projectConfig['name']

    @property
    def baseDir(self):
        return self.projectConfig['baseDir']

    def __str__(self):
        return self.name

    def setGlobalProject(self):
        global currentProject
        currentProject=self

    @staticmethod
    def attemptDatabaseConnection(dbConn):
        """Attempt to connect to the database"""
        logger = logging.getLogger(__name__)
        try:
            engine = create_engine(dbConn.connectionString, echo=dbConn.echo)
            engine.connect()
            engine.dispose()
            success = True
            logger.info("Database connection successful")
        except Exception:
            success = False
            logger.info("Database connection failed - please check settings")
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


class ProjectException(Exception):
    pass


def getProject():
    if not currentProject:
        raise ProjectException('No project set')
    return currentProject



if __name__ == '__main__':
    import sys
    logging.basicConfig(level=logging.DEBUG)
    app = QtGui.QApplication(sys.argv)
    project = Project()