# -*- coding: utf-8 -*-
"""
Created on Fri May 10 21:02:42 2013

@author: pmaunz
"""

import os.path
import __main__
from modules.configshelve import configshelve
from modules import DataDirectory

ProjectsBaseDir = os.path.expanduser("~public\\Documents\\experiments")
Project = None
DefaultProject = None
DefaultProjectCached = False

with configshelve(os.path.basename(__main__.__file__)+"-project") as config:
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
            with configshelve(os.path.basename(__main__.__file__)+"-project") as config:
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
        with configshelve(os.path.basename(__main__.__file__)+"-project") as config:
            config['DefaultProject'] = name
    DefaultProjectCached = True

def setProject(project):
    global Project
    Project = project
    
def projectDir():
    return os.path.join(ProjectsBaseDir, Project) if Project else None
    
def configDir():
    configDir = os.path.join(ProjectsBaseDir, Project, 'config') if Project else None
    if not os.path.exists(configDir):
        os.makedirs(configDir)
    return configDir
    
def getBaseDir():
    return ProjectsBaseDir
    
def setProjectBaseDir(name,atStartup=False):
    with configshelve(os.path.basename(__main__.__file__)+"-project") as config:
        config['ProjectBaseDir'] = name
    if atStartup:
        global ProjectsBaseDir
        ProjectsBaseDir = name
        DataDirectory.DataDirectoryBase = name
    
    
    