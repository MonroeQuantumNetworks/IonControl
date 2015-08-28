from sys import path

class chassisPaths(object):
    def __init__(self):
        pass

    @staticmethod
    def addPaths():
        myPaths = ['C:\\Workspace\\Chassis.git',
                'C:\\Workspace\\Chassis.git\\tests',
                'C:\\Workspace\\Chassis.git\\examples']
        for myPath in myPaths:
            for pyPath in path:
                exists = False
                print pyPath, myPath
                if pyPath == myPath:
                    exists = True
                    break

            if exists == False:
                path.insert(1, myPath)

