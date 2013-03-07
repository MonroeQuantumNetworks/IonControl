# -*- coding: utf-8 -*-
"""
Created on Sun Feb 24 16:41:05 2013

@author: pmaunz
"""

from pyparsing import Literal,CaselessLiteral,Word,Combine,Optional,\
    nums,alphas,ParseException
import magnitude

point = Literal( "." )
e     = CaselessLiteral( "E" )
fnumber = Combine( Word( "+-"+nums, nums ) + 
                   Optional( point + Optional( Word( nums ) ) ) +
                   Optional( e + Word( "+-"+nums, nums ) ) )
ident = Word(alphas, alphas+nums+"_$")

valueexpr = ( fnumber + Optional(ident)  )
precisionexpr = (  Word( "+-"+nums, nums ) + Optional(point + Optional(Word( nums, nums ))) )

def parse( string ):
    val = valueexpr.parseString( string )
    precres = precisionexpr.parseString( string )
    prec = len(precres[2]) if len(precres)==3 else 0
    retval = magnitude.mg(float(val[0]),val[1])
    retval.output_prec( prec )
    return retval

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
    delta = decimalpos-mydeltapos
    return retval, magnitude.mg(pow(10,delta),unit), deltapos
    
def positionawareTrim( string, position ):
    oldlen = len(string)
    string = string.lstrip()
    newlen = len(string)
    return string.rstrip(), min(max(position - oldlen + newlen,0), newlen)


if __name__=="__main__":
    print positionawareTrim('   1234',10)
    for line in ['12MHz', '12.123456789 MHz','-200.234e3 us','   12.000 MHz']:
        try:
            print line, "->"
            for elem in parseDelta(line, 4):
                print elem
            print
        except ParseException as e:
            print "not a full match", e
     