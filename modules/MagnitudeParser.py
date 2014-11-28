# -*- coding: utf-8 -*-
"""
Created on Sun Feb 24 16:41:05 2013

Parser for magnitude expressions. Can parse arithmetic expressions with values including standard si units.

@author: pmaunz
"""

from pyparsing import Literal,CaselessLiteral,Word,Combine,Optional,\
    nums,alphas

import modules.magnitude as magnitude
from modules.lru_cache import lru_cache

point = Literal( "." )
e     = CaselessLiteral( "E" )
plus  = Literal( "+" )
minus = Literal( "-" )
dotNumber = Combine( Optional(plus | minus) + point + Word(nums)+
                   Optional( e + Word( "+-"+nums, nums ) ) )
numfnumber = Combine( Optional(plus | minus) + Word( nums ) + 
                   Optional( point + Optional( Word( nums ) ) ) +
                   Optional( e + Word( "+-"+nums, nums ) ) )
fnumber = numfnumber | dotNumber
ident = Word(alphas, alphas+nums+"_$")

valueexpr = ( fnumber + Optional(ident)  )
precisionexpr = (  Word( "+-"+nums, nums ) + Optional(point + Optional(Word( nums, nums ))) )

@lru_cache(maxsize=100)
def parse( string ):
    val = valueexpr.parseString( string )
    precres = precisionexpr.parseString( string )
    prec = len(precres[2]) if len(precres)==3 else 0
    retval = magnitude.mg(float(val[0]),val[1] if len(val)>1 else None)
    retval.output_prec( prec )
    return retval

@lru_cache(maxsize=100)
def parseDelta( string, deltapos=0, parseAll=True ):
    string, deltapos = positionawareTrim(string,deltapos)
    val = valueexpr.parseString( string , parseAll=parseAll )
    precres = precisionexpr.parseString( string )
    prec = len(precres[2]) if len(precres)==3 else 0
    decimalpos = len(precres[0])
    mydeltapos = max( 2 if precres[0][0]=='-' else 1, min( deltapos-(1 if deltapos>decimalpos else 0), decimalpos+prec ))
    unit = val[1] if len(val)>1 else ''
    retval = magnitude.mg(float(val[0]),unit)
    retval.output_prec( prec )
    retval.significantDigits = len(list(filter( lambda s: s.isdigit(), val[0].lstrip("-0.") )))
    delta = decimalpos-mydeltapos
    return retval, magnitude.mg(pow(10,delta),unit), deltapos, decimalpos
    
@lru_cache(maxsize=100)
def isValueExpression( text ):
    try:
        valueexpr.parseString( text , parseAll=True )
        return True
    except Exception:
        pass
    return False
    
def positionawareTrim( string, position ):
    oldlen = len(string)
    string = string.lstrip()
    newlen = len(string)
    return string.rstrip(), min(max(position - oldlen + newlen,0), newlen)


if __name__=="__main__":
    print isValueExpression('2kHz')
#     print positionawareTrim('   1234',10)
#     for line in ['12MHz', '12.123456789 MHz','-200.234e3 us','   12.000 MHz','40']:
#         try:
#             print line, "->"
#             for elem in parseDelta(line, 4):
#                 print elem
#             print
#         except ParseException as e:
#             print "not a full match", e
#      
