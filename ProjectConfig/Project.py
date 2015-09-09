"""
Created on 09 Sep 2015 at 2:26 PM

@author: jmizrahi
"""

import os.path
import yaml

class Project(object):
    def __init__(self):
        """initialize a project by loading in the project config information"""
        mainDir = os.path.join(os.path.dirname(__file__), '..') #Main IonControl directory
        filename = 'config/ProjectConfig.yml' #path to config file
        projectConfigFilename = os.path.join(mainDir, filename)
        with open(projectConfigFilename, 'r') as f:
            self.__dict__.update(yaml.load(f)) #load in config information

        self.projectDir = os.path.join(self.baseDir, self.name)
        if not os.path.exists(self.projectDir): #invalid paths must show GUI
            self.showGui = True

        if self.showGui:
            


if __name__ == '__main__':
    project = Project()


