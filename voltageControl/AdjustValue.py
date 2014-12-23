'''
Created on Dec 10, 2014

@author: pmaunz
'''
from modules.Expression import Expression
from gui.ExpressionValue import ExpressionValue

class AdjustValue(ExpressionValue):
    expression = Expression()
    def __init__(self, name=None, line=0, globalDict=None):
        super(self, AdjustValue ).__init__(name, globalDict)
        self.line = line
        
