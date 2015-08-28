'''
Created on Dec 10, 2014

@author: pmaunz
'''
from modules.Expression import Expression
from gui.ExpressionValue import ExpressionValue   #@UnresolvedImport

class AdjustValue(ExpressionValue):
    expression = Expression()
    def __init__(self, name=None, line=0, globalDict=None):
        ExpressionValue.__init__(self, name, globalDict)
        self.line = line
        
    def __hash__(self):
        return hash(self.value)
        
