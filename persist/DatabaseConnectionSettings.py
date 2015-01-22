'''
Created on Dec 2, 2014

@author: pmaunz
'''



class DatabaseConnectionSettings(object):
    def __init__(self, **kwargs):
        self.user = kwargs.get('user', "")
        self.password = kwargs.get('password', "")
        self.database = kwargs.get('database', "")
        self.host = kwargs.get('host', "")
        self.port = kwargs.get('port', 5432)
        self.echo = kwargs.get('echo', False )
        
    @property
    def connectionString(self):
        return "postgresql://{user}:{password}@{host}:{port}/{database}".format(**self.__dict__)

DatabaseConectionSettings = DatabaseConnectionSettings