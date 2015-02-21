# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'PulseProgramEdit.ui'
#
# Created: Fri Feb 20 20:17:34 2015
#      by: PyQt4 UI code generator 4.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui
from QPPPEditor import QPPPEditor

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(_fromUtf8("Form"))
        Form.resize(605, 423)
        self.verticalLayout = QtGui.QVBoxLayout(Form)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.textEdit = QPPPEditor(Form)
        self.textEdit.setToolTip(_fromUtf8(""))
        self.textEdit.setWhatsThis(_fromUtf8(""))
        self.textEdit.setObjectName(_fromUtf8("textEdit"))
        self.verticalLayout.addWidget(self.textEdit)
        self.errorDisplay = QtGui.QFrame(Form)
        self.errorDisplay.setAutoFillBackground(False)
        self.errorDisplay.setStyleSheet(_fromUtf8("QWidget {background: #ff8080; }"))
        self.errorDisplay.setFrameShape(QtGui.QFrame.StyledPanel)
        self.errorDisplay.setFrameShadow(QtGui.QFrame.Raised)
        self.errorDisplay.setObjectName(_fromUtf8("errorDisplay"))
        self.horizontalLayout_5 = QtGui.QHBoxLayout(self.errorDisplay)
        self.horizontalLayout_5.setSpacing(6)
        self.horizontalLayout_5.setMargin(0)
        self.horizontalLayout_5.setObjectName(_fromUtf8("horizontalLayout_5"))
        self.closeErrorButton = QtGui.QToolButton(self.errorDisplay)
        self.closeErrorButton.setMinimumSize(QtCore.QSize(22, 22))
        self.closeErrorButton.setMaximumSize(QtCore.QSize(22, 22))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/openicon/icons/edit-delete-6.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.closeErrorButton.setIcon(icon)
        self.closeErrorButton.setIconSize(QtCore.QSize(22, 22))
        self.closeErrorButton.setAutoRaise(True)
        self.closeErrorButton.setObjectName(_fromUtf8("closeErrorButton"))
        self.horizontalLayout_5.addWidget(self.closeErrorButton)
        self.errorLabel = QtGui.QLabel(self.errorDisplay)
        self.errorLabel.setObjectName(_fromUtf8("errorLabel"))
        self.horizontalLayout_5.addWidget(self.errorLabel)
        spacerItem = QtGui.QSpacerItem(31, 19, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem)
        self.verticalLayout.addWidget(self.errorDisplay)
        self.findWidgetFrame = QtGui.QFrame(Form)
        self.findWidgetFrame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.findWidgetFrame.setFrameShadow(QtGui.QFrame.Raised)
        self.findWidgetFrame.setObjectName(_fromUtf8("findWidgetFrame"))
        self.horizontalLayout_4 = QtGui.QHBoxLayout(self.findWidgetFrame)
        self.horizontalLayout_4.setSpacing(6)
        self.horizontalLayout_4.setMargin(0)
        self.horizontalLayout_4.setObjectName(_fromUtf8("horizontalLayout_4"))
        self.findCloseButton = QtGui.QToolButton(self.findWidgetFrame)
        self.findCloseButton.setMinimumSize(QtCore.QSize(22, 22))
        self.findCloseButton.setMaximumSize(QtCore.QSize(22, 22))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/openicon/icons/window-close.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.findCloseButton.setIcon(icon1)
        self.findCloseButton.setIconSize(QtCore.QSize(22, 22))
        self.findCloseButton.setAutoRaise(True)
        self.findCloseButton.setObjectName(_fromUtf8("findCloseButton"))
        self.horizontalLayout_4.addWidget(self.findCloseButton)
        self.label = QtGui.QLabel(self.findWidgetFrame)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout_4.addWidget(self.label)
        self.findLineEdit = QtGui.QLineEdit(self.findWidgetFrame)
        self.findLineEdit.setObjectName(_fromUtf8("findLineEdit"))
        self.horizontalLayout_4.addWidget(self.findLineEdit)
        self.findNextButton = QtGui.QToolButton(self.findWidgetFrame)
        self.findNextButton.setMinimumSize(QtCore.QSize(0, 22))
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8(":/openicon/icons/go-down-7.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.findNextButton.setIcon(icon2)
        self.findNextButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.findNextButton.setAutoRaise(True)
        self.findNextButton.setObjectName(_fromUtf8("findNextButton"))
        self.horizontalLayout_4.addWidget(self.findNextButton)
        self.findPreviousButton = QtGui.QToolButton(self.findWidgetFrame)
        self.findPreviousButton.setMinimumSize(QtCore.QSize(0, 22))
        icon3 = QtGui.QIcon()
        icon3.addPixmap(QtGui.QPixmap(_fromUtf8(":/openicon/icons/go-up-7.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.findPreviousButton.setIcon(icon3)
        self.findPreviousButton.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.findPreviousButton.setAutoRaise(True)
        self.findPreviousButton.setObjectName(_fromUtf8("findPreviousButton"))
        self.horizontalLayout_4.addWidget(self.findPreviousButton)
        self.findMatchCaseCheckBox = QtGui.QCheckBox(self.findWidgetFrame)
        self.findMatchCaseCheckBox.setObjectName(_fromUtf8("findMatchCaseCheckBox"))
        self.horizontalLayout_4.addWidget(self.findMatchCaseCheckBox)
        self.findWholeWordsCheckBox = QtGui.QCheckBox(self.findWidgetFrame)
        self.findWholeWordsCheckBox.setObjectName(_fromUtf8("findWholeWordsCheckBox"))
        self.horizontalLayout_4.addWidget(self.findWholeWordsCheckBox)
        spacerItem1 = QtGui.QSpacerItem(31, 19, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout_4.addItem(spacerItem1)
        self.verticalLayout.addWidget(self.findWidgetFrame)
        self.actionFind = QtGui.QAction(Form)
        self.actionFind.setObjectName(_fromUtf8("actionFind"))

        self.retranslateUi(Form)
        QtCore.QObject.connect(self.actionFind, QtCore.SIGNAL(_fromUtf8("triggered()")), self.findWidgetFrame.show)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        Form.setWindowTitle(_translate("Form", "Form", None))
        self.closeErrorButton.setText(_translate("Form", "...", None))
        self.errorLabel.setText(_translate("Form", "TextLabel", None))
        self.findCloseButton.setText(_translate("Form", "...", None))
        self.label.setText(_translate("Form", "Find:", None))
        self.findNextButton.setText(_translate("Form", "Next", None))
        self.findPreviousButton.setText(_translate("Form", "Previous", None))
        self.findMatchCaseCheckBox.setText(_translate("Form", "Match case", None))
        self.findWholeWordsCheckBox.setText(_translate("Form", "Whole words", None))
        self.actionFind.setText(_translate("Form", "find", None))
        self.actionFind.setShortcut(_translate("Form", "Ctrl+F", None))

import Experiment_rc
