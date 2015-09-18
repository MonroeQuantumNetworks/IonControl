"""
Created on 17 Sep 2015 at 2:10 PM

@author: jmizrahi
"""

from PyQt4 import QtGui
import sys

def importErrorPopup(moduleName):
    messageBox = QtGui.QMessageBox()
    response = messageBox.warning(messageBox,
                                  'Import Failure',
                                  '{0} module is listed as enabled in the configuration file, but the import failed. Proceed without?'.format(moduleName),
                                  QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Ok)
    if response!=QtGui.QMessageBox.Ok:
        sys.exit('{0} import failure'.format(moduleName))

if __name__=='__main__':
    app = QtGui.QApplication(sys.argv)
    importErrorPopup('myModule')