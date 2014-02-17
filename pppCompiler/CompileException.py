'''
Created on Feb 15, 2014

@author: pmaunz
'''

from pyparsing import ParseBaseException

class CompileException(ParseBaseException):
    """Exception for compiler errors including the location information
    ParseBaseException falls through to the basic pyparsing parse procedure,
    the long internal stacktrace is removed and the exception re-raised"""
    pass

class CompileInternalException(Exception):
    """Exception for compiler errors where location information is not available"""
    pass

class SymbolException(CompileInternalException):
    pass

