'''
Created on Feb 15, 2014

@author: pmaunz
'''

from pyparsing import ParseBaseException, line, lineno, col

class CompileException(ParseBaseException):
    """Exception for compiler errors including the location information
    ParseBaseException falls through to the basic pyparsing parse procedure,
    the long internal stacktrace is removed and the exception re-raised"""
    def line(self):
        return line( self.loc, self.pstr )
    
    def col(self):
        return col( self.loc, self.pstr )
    
    def lineno(self):
        return lineno( self.loc, self.pstr )
    
    def message(self):
        return self.msg
    
class CompileInternalException(Exception):
    """Exception for compiler errors where location information is not available"""
    pass

class SymbolException(CompileInternalException):
    pass

