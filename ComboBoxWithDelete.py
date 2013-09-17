# -*- coding: utf-8 -*-
"""
Created on Thu May 09 13:48:16 2013

@author: wolverine
"""
from PyQt4 import QtCore, QtGui


class ComboBoxWithDelete( QtGui.QComboBox ):
    def __init__(self, parent=0):
        QtGui.QComboBox.__init__(self,parent)
        
    def keyReleaseEvent(self, e):
        print "key released"
        QtGui.QComboBox.keyReleaseEvent(self,e)




if __name__ == "__main__":
    try:
        _fromUtf8 = QtCore.QString.fromUtf8
    except AttributeError:
        _fromUtf8 = lambda s: s
    
    class Ui_Form(object):
        def setupUi(self, Form):
            Form.setObjectName(_fromUtf8("Form"))
            Form.resize(400, 123)
            self.gridLayout = QtGui.QGridLayout(Form)
            self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
            self.pushButton = QtGui.QPushButton(Form)
            self.pushButton.setObjectName(_fromUtf8("pushButton"))
            self.gridLayout.addWidget(self.pushButton, 0, 1, 1, 1)
            self.comboBox = ComboBoxWithDelete(Form)
            self.comboBox.setObjectName(_fromUtf8("comboBox"))
            self.gridLayout.addWidget(self.comboBox, 1, 0, 1, 1)
            self.lineEdit = QtGui.QLineEdit(Form)
            self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
            self.gridLayout.addWidget(self.lineEdit, 0, 0, 1, 1)
            spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
            self.gridLayout.addItem(spacerItem, 2, 0, 1, 1)
    
            self.retranslateUi(Form)
            QtCore.QMetaObject.connectSlotsByName(Form)
            self.pushButton.clicked.connect( self.onAdd )
    
        def retranslateUi(self, Form):
            Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
            self.pushButton.setText(QtGui.QApplication.translate("Form", "Add", None, QtGui.QApplication.UnicodeUTF8))

        def onAdd(self):
            self.comboBox.addItem( self.lineEdit.text() )
            self.lineEdit.clear()

    import sys
    app = QtGui.QApplication(sys.argv)
    Form = QtGui.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec_())
