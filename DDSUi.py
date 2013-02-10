from PyQt4 import QtGui, QtCore
import PyQt4.uic

DDSForm, DDSBase = PyQt4.uic.loadUiType(r'ui\DDS.ui')

class DDSUi(DDSForm, DDSBase):
    def __init__(self,parent=None):
        DDSBase.__init__(self,parent)
        DDSForm.__init__(self,parent)
        
    def setupUi(self,parent):
        DDSForm.setupUi(self,parent)

        
if __name__ == "__main__":
    import sys
    app = QtGui.QApplication(sys.argv)
    ui = DDSUi()
    ui.setupUi(ui)
    ui.show()
    sys.exit(app.exec_())
