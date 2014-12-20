'''
Created on Dec 19, 2014

@author: pmaunz
'''


        self.pushTableModel = PushVariableTableModel(self.config, self.globalDict)
        self.pushTableView.setModel( self.pushTableModel )
        self.pushItemDelegate = MagnitudeSpinBoxDelegate(self.globalDict)
        self.pushComboDelegate = ComboBoxDelegate()
        self.pushTableView.setItemDelegateForColumn(1,self.pushComboDelegate)
        self.pushTableView.setItemDelegateForColumn(2,self.pushComboDelegate)
        self.pushTableView.setItemDelegateForColumn(3,self.pushItemDelegate)
        self.pushTableView.setItemDelegateForColumn(4,self.pushItemDelegate)
        self.pushTableView.setItemDelegateForColumn(5,self.pushItemDelegate)
        self.pushTableView.setItemDelegateForColumn(6,self.pushItemDelegate)
        self.pushDestinations['Database'] = DatabasePushDestination('fit')

    def onAddPushVariable(self):
        self.pushTableModel.addVariable( PushVariable() )
    
    def onRemovePushVariable(self):
        for index in sorted(unique([ i.row() for i in self.pushTableView.selectedIndexes() ]),reverse=True):
            self.pushTableModel.removeVariable(index)
             
        self.fitfunction.updatePushVariables( self.globalDict )
        self.pushTableModel.setFitfunction(self.fitfunction)

    def addPushDestination(self, name, destination ):
        self.pushDestinations[name] = destination
        self.pushTableModel.updateDestinations(self.pushDestinations )

    def onPush(self):
        for destination, variable, value in self.fitfunction.pushVariableValues(self.globalDict):
            if destination in self.pushDestinations:
                self.pushDestinations[destination].update( [(destination,variable,value)] )
                
    def pushVariables(self, pushVariables):
        for destination, variable, value in pushVariables:
            if destination in self.pushDestinations:
                self.pushDestinations[destination].update( [(destination,variable,value)] )

