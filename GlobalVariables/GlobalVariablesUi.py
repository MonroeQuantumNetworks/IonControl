"""
Created on 05 Nov 2015 at 3:52 PM

author: jmizrahi
"""
from PyQt4 import QtGui, QtCore
import PyQt4.uic

from GlobalVariablesModel import GlobalVariablesModel, MagnitudeSpinBoxGridDelegate, GridDelegate
from GlobalVariable import GlobalVariable, GlobalVariablesLookup
from modules.GuiAppearance import restoreGuiState, saveGuiState   #@UnresolvedImport
from modules.XmlUtilit import xmlEncodeDictionary, xmlParseDictionary, prettify
import xml.etree.ElementTree as ElementTree
from modules import DataDirectory
from functools import partial
import logging
import os
from copy import copy

from uiModules.MagnitudeSpinBoxDelegate import MagnitudeSpinBoxDelegate

uipath = os.path.join(os.path.dirname(__file__), '..', r'ui\\GlobalVariables.ui')
Form, Base = PyQt4.uic.loadUiType(uipath)

class GlobalVariablesUi(Form, Base):
    """Class for displaying, adding, and modifying global variables"""
    def __init__(self, config, preferences, parent=None):
        Form.__init__(self)
        Base.__init__(self, parent)
        self.config = config
        self.configName = 'GlobalVariables'
        try:
            storedGlobals = self.config.get(self.configName, dict())
            if storedGlobals.__class__==list: #port over globals stored as a list
                storedGlobals = {g.name:g for g in storedGlobals}
        except:
            storedGlobals = dict()
        self._globalDict_ = storedGlobals
        self.globalDict = GlobalVariablesLookup(self._globalDict_)
        self.guiPreferences = preferences.guiPreferences

    @property
    def valueChanged(self):
        return self.model.valueChanged

    def keys(self):
        return self.globalDict.keys()

    def setupUi(self, parent):
        Form.setupUi(self,parent)
        self.model = GlobalVariablesModel(self.config, self._globalDict_)
        self.view.setModel(self.model)
        self.nameDelegate = QtGui.QStyledItemDelegate() if self.guiPreferences.useCondensedGlobalTree else GridDelegate()
        self.valueDelegate = MagnitudeSpinBoxDelegate() if self.guiPreferences.useCondensedGlobalTree else MagnitudeSpinBoxGridDelegate()
        self.view.setItemDelegateForColumn(self.model.column.name, self.nameDelegate)
        self.view.setItemDelegateForColumn(self.model.column.value, self.valueDelegate)
        restoreGuiState( self, self.config.get(self.configName+".guiState") )
        try:
            self.view.restoreTreeState( self.config.get(self.configName+'.treeState', None) )
        except Exception as e:
            logging.getLogger(__name__).error("unable to restore tree state in {0}: {1}".format(self.configName, e))

        #signals
        self.newNameEdit.returnPressed.connect( self.onAddVariable )
        self.addButton.clicked.connect( self.onAddVariable )
        self.dropButton.clicked.connect( self.view.onDelete )
        self.exportXmlButton.clicked.connect( self.onExportXml )
        self.collapseAllButton.clicked.connect( self.view.collapseAll )
        self.expandAllButton.clicked.connect( self.view.expandAll )
        self.model.globalRemoved.connect( self.refreshCategories )

        #Categorize Context Menu
        self.setContextMenuPolicy( QtCore.Qt.ActionsContextMenu )
        categorizeAction = QtGui.QAction("Categorize", self)
        self.categorizeMenu = QtGui.QMenu(self)
        categorizeAction.setMenu(self.categorizeMenu)
        self.addAction(categorizeAction)
        self.categoriesListModel = QtGui.QStringListModel()
        self.categoriesListComboBox.setModel(self.categoriesListModel)
        self.refreshCategories()

        #background color context menu
        backgroundColorAction = QtGui.QAction("Background Color", self)
        backgroundColorMenu = QtGui.QMenu(self)
        backgroundColorAction.setMenu(backgroundColorMenu)
        self.addAction(backgroundColorAction)
        setBackgroundColorAction = QtGui.QAction("Set Background Color", self)
        setBackgroundColorAction.triggered.connect(self.view.onSetBackgroundColor)
        backgroundColorMenu.addAction(setBackgroundColorAction)
        removeBackgroundColorAction = QtGui.QAction("Remove Background Color", self)
        removeBackgroundColorAction.triggered.connect(self.view.onRemoveBackgroundColor)
        backgroundColorMenu.addAction(removeBackgroundColorAction)

        #sort context action
        sortAction = QtGui.QAction("Sort", self)
        self.addAction(sortAction)
        sortAction.triggered.connect(partial(self.view.sortByColumn, self.model.column.name, QtCore.Qt.DescendingOrder))

    def refreshCategories(self):
        """Set up the categories context menu and combo box"""
        self.categorizeMenu.clear()
        newCategoryAction = QtGui.QAction("New category", self)
        self.categorizeMenu.addAction(newCategoryAction)
        newCategoryAction.triggered.connect(self.onNewCategory)
        noCategoryAction = QtGui.QAction("No category", self)
        noCategoryAction.triggered.connect(partial(self.onCategorize, None))
        self.categorizeMenu.addAction(noCategoryAction)
        self.categoriesList = ['']
        self.categoriesListModel.setStringList(self.categoriesList)
        for var in self._globalDict_.values():
            categories = copy(var.categories)
            if categories:
                categories = [categories] if categories.__class__!=list else categories # make a list of one if it's not a list
                categories = map(str, categories) #make sure it's a list of strings
                categories = '.'.join(categories)
                self.addCategories(categories)

    def addCategories(self, categories):
        """add the specified categories to the context menu and combo box
        Args:
            categories (str): a single category, or a dotted string containing a list of categories (a.b.c)
            """
        if categories not in self.categoriesList:
            self.categoriesList.append(categories)
            self.categoriesListModel.setStringList(self.categoriesList)
            action = QtGui.QAction(categories, self)
            self.categorizeMenu.addAction(action)
            action.triggered.connect(partial(self.onCategorize, categories))

    def onNewCategory(self):
        """new category action selected from context menu"""
        categories, ok = QtGui.QInputDialog.getText(self, 'New category', 'Please enter new category(ies) (dot sub-categories: cat1.cat2.cat3): ')
        if ok:
            categories = str(categories).strip('.')
            self.addCategories(categories)
            self.onCategorize(categories)

    def onCategorize(self, categories):
        """categorize the selected nodes under 'categories'
        Args:
            categories (str): a single category, or a dotted string containing a list of categories (a.b.c)
            """
        if categories:
            categories = categories.split('.')
        nodes = self.view.selectedNodes()
        for node in nodes:
            self.model.changeCategory(node, categories)
            self.view.expandToNode(node)
        self.refreshCategories()

    def onExportXml(self, element=None, writeToFile=True):
        root = element if element is not None else ElementTree.Element('GlobalVariables')
        xmlEncodeDictionary(self.globalDict, root, "Variable")
        if writeToFile:
            filename = DataDirectory.DataDirectory().sequencefile("GlobalVariables.xml")[0]
            with open(filename,'w') as f:
                f.write(prettify(root))
        return root

    def onImportXml(self, filename=None, mode="Add"):
        filename = filename if filename is not None else QtGui.QFileDialog.getOpenFileName(self, 'Import XML file', filer="*.xml" )
        tree = ElementTree.parse(filename)
        element = tree.getroot()
        self.importXml(element, mode=mode)

    def importXml(self, element, mode="Add"):   # modes: replace, update, Add
        """import global variables from XML file.
        Args:
            element: root of XML tree
            mode: how to add in global variables:

                - Add: add any missing global variables, leave existing global variables untouched.
                - Update: As 'Add', but also change values of existing global variables based on file.
                - Replace: As 'Update', but also remove any global variables not found in file.
        """
        newGlobalDict = xmlParseDictionary(element, "Variable")
        self.model.beginResetModel()

        #add new globals, applicable to all modes
        for name, value in newGlobalDict.iteritems():
            if name not in self._globalDict_:
                self._globalDict_[name] = GlobalVariable(name, value)
            if mode=="Replace" or mode=="Update": #update existing globals
                self._globalDict_[name].value = value

        #clear out globals that don't appear in file
        if mode=="Replace":
            for name in self._globalDict_:
                if name not in newGlobalDict:
                    del self._globalDict_[name]

        self.model.clear()
        self.model.addNodeList(self._globalDict_.values())
        self.model.endResetModel()

    def onAddVariable(self):
        """A new variable is added via the UI, either by typing in a name and pressing enter, or by clicking add."""
        name = str(self.newNameEdit.text())
        categories = str(self.categoriesListComboBox.currentText())
        categories = categories.strip('.')
        node = self.model.addVariable(name, categories.split('.'))
        if node:
            self.view.expandToNode(node)
        self.newNameEdit.setText("")
        self.addCategories(categories)
        blankInd = self.categoriesListComboBox.findText('', QtCore.Qt.MatchExactly)
        self.categoriesListComboBox.setCurrentIndex(blankInd)

    def saveConfig(self):
        """save gui configuration state and _globalDict_"""
        self.config[self.configName] = self._globalDict_
        self.config[self.configName+".guiState"] = saveGuiState(self)
        try:
            self.config[self.configName+'.treeState'] = self.view.treeState()
        except Exception as e:
            logging.getLogger(__name__).error("unable to save tree state in {0}: {1}".format(self.configName, e))

    def update(self, updlist):
        """Update list of globals"""
        self.model.update(updlist)


if __name__=="__main__":
    import sys
    config = dict()
    app = QtGui.QApplication(sys.argv)
    MainWindow = QtGui.QMainWindow()
    ui = GlobalVariableUi(config)
    ui.setupUi(ui)
    MainWindow.setCentralWidget(ui)
    MainWindow.show()
    sys.exit(app.exec_())
