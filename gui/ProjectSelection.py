# -*- coding: utf-8 -*-
"""
Created on Fri May 10 21:02:42 2013

@author: pmaunz
"""

import __main__
import os.path

from modules import DataDirectory
from persist.configshelve import configshelve


ProjectsBaseDir = os.path.expanduser("~public\\Documents\\experiments")
Project = None
DefaultProject = None
DefaultProjectCached = False
SpecificConfigFile = None    # if nont none will be used instaed of the default

class ProjectException(Exception):
    pass

if hasattr(__main__,'__file__'):
    with configshelve(os.path.basename(__main__.__file__)+"-project.db") as config:
        DefaultProject = config.get('DefaultProject')
        ProjectsBaseDir = config.get('ProjectBaseDir',ProjectsBaseDir)
        DataDirectory.DataDirectoryBase = ProjectsBaseDir
    DefaultProjectCached = True


def checkProjectsDir():
    if not os.path.exists(ProjectsBaseDir):
        os.makedirs(ProjectsBaseDir)
    
def projects():
    checkProjectsDir()
    return [name for name in os.listdir(ProjectsBaseDir)
            if os.path.isdir(os.path.join(ProjectsBaseDir, name))]
    
def defaultProject():
    global DefaultProject
    global DefaultProjectCached
    if not DefaultProjectCached:
        if hasattr(__main__,'__file__'):
            with configshelve(os.path.basename(__main__.__file__)+"-project.db") as config:
                DefaultProject = config.get('DefaultProject')
            DefaultProjectCached = True
    return DefaultProject
    
def createProject(name):
    os.mkdir(os.path.join(ProjectsBaseDir, name))
    
def setDefaultProject(name):
    global DefaultProjectCached
    global DefaultProject
    DefaultProject = name
    if hasattr(__main__,'__file__'):
        with configshelve(os.path.basename(__main__.__file__)+"-project.db") as config:
            config['DefaultProject'] = name
    DefaultProjectCached = True

def setProject(project):
    global Project
    Project = project
    
def projectDir():
    return os.path.join(ProjectsBaseDir, Project) if Project else None
    
def configDir():
    if not Project:
        raise ProjectException("no Project set")
    configDir = os.path.join(ProjectsBaseDir, Project, 'config') 
    if not os.path.exists(configDir):
        os.makedirs(configDir)
    return configDir

def guiConfigDir():
    if not Project:
        raise ProjectException("no Project set")
    configDir = os.path.join(ProjectsBaseDir, Project, '.gui-config') 
    if not os.path.exists(configDir):
        os.makedirs(configDir)
    return configDir

def guiConfigFile():
    global SpecificConfigFile
    if SpecificConfigFile:
        return SpecificConfigFile
    else:
        return os.path.join( guiConfigDir(), "experiment-gui.db.config" ) 
   
def getBaseDir():
    return ProjectsBaseDir
    
def setProjectBaseDir(name,atStartup=False):
    with configshelve(os.path.basename(__main__.__file__)+"-project.db") as config:
        config['ProjectBaseDir'] = name
    if atStartup:
        global ProjectsBaseDir
        ProjectsBaseDir = name
        DataDirectory.DataDirectoryBase = name
    
def setSpecificConfigFile(name):
    global SpecificConfigFile
    if name:
        SpecificConfigFile = name
    else: 
        SpecificConfigFile = None

    