# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'VoltageGlobalAdjust.ui'
#
# Created: Tue Mar 19 22:37:48 2013
#      by: PyQt4 UI code generator 4.9.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(165, 300)
        self.gridLayout = QtGui.QGridLayout(Form)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.doubleSpinBox = MagnitudeSpinBox(Form)
        self.doubleSpinBox.setObjectName(_fromUtf8("doubleSpinBox"))
        self.gridLayout.addWidget(self.doubleSpinBox, 1, 2, 1, 1)
        self.label = QtGui.QLabel(Form)
        self.label.setObjectName(_fromUtf8("label"))
        self.gridLayout.addWidget(self.label, 1, 1, 1, 1)
        self.label_2 = QtGui.QLabel(Form)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.gridLayout.addWidget(self.label_2, 0, 1, 1, 1)
        self.label_3 = QtGui.QLabel(Form)
        self.label_3.setObjectName(_fromUtf8("label_3"))
        self.gridLayout.addWidget(self.label_3, 0, 2, 1, 1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem, 2, 1, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtGui.QApplication.translate("Form", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Form", "Gain", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Form", "Parameter", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("Form", "Contribution", None, QtGui.QApplication.UnicodeUTF8))

from MagnitudeSpinBox import MagnitudeSpinBox
