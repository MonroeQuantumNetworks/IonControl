'''
Created on Dec 2, 2014

@author: pmaunz
'''



class DatabaseConectionSettings(object):
    def __init__(self):
        self.user = ""
        self.password = ""
        self.database = ""
        self.host = ""
        self.port = 5432
        self.echo = False
        
    @property
    def connectionString(self):
        return "postgresql://{user}:{password}@{host}:{port}/{database}".format(**self.__dict__)
        