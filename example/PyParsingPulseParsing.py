# -*- coding: utf-8 -*-
"""
Created on Sun Feb 24 16:41:05 2013

@author: pmaunz
"""

from pyparsing import Literal,CaselessLiteral,Word,Combine,Group,Optional,\
    ZeroOrMore,Forward,nums,alphas,restOfLine, printables, Suppress, OneOrMore, Keyword

point = Literal( "." )
comma = Literal(",")
e     = CaselessLiteral( "E" )
fnumber = Combine( Word( "+-"+nums, nums ) + 
                   Optional( point + Optional( Word( nums ) ) ) +
                   Optional( e + Word( "+-"+nums, nums ) ) )
inumber =  Word( "+-"+nums, nums )
ident = Word(alphas, alphas+nums+"_$")
funit = Combine( fnumber + Optional(Word(" "," ")) + ident )
anything = Word( alphas+nums , alphas+nums )

def onZero(strg, loc, toks ):
    print "onZero", strg, loc, toks, number


comment = Word( "#", printables )
varLiteral = CaselessLiteral("var")
varExpression = varLiteral + ident + anything + ZeroOrMore( Suppress(comma) + Group( ZeroOrMore(anything)) )+ Suppress( Optional( comment + restOfLine ) )
defineLiteral = CaselessLiteral("#define")
defineExpression = defineLiteral + ident + inumber + Suppress( Optional( comment + restOfLine ) )
operatorExpression = ident + Optional( ident ) + ZeroOrMore( Suppress(comma) + ident ) + Suppress( Optional( comment + restOfLine ) )
label = ident + Suppress(Literal(":")) + operatorExpression
commentLine = comment + restOfLine
macro = Keyword("macro")

def onVar(strg, loc, toks ):
    print "onVar", strg, loc, toks, number

def onDefine(strg, loc, toks ):
    print "onDefine", strg, loc, toks, number
    
def onOperator(strg, loc, toks ):
    print "onOperator", strg, loc, toks, number

def onLabel(strg, loc, toks ):
    print "onLabel", strg, loc, toks, number



expression = ( varExpression.setParseAction( onVar ) | 
               defineExpression.setParseAction( onDefine ) | 
               label.setParseAction( onLabel ) |
               operatorExpression.setParseAction( onOperator ) |
               commentLine )



if __name__=="__main__":
    with open(r"C:\Users\pmaunz\Documents\Programming\aaAQC_FPGA\prog\Ions\ScanParameter.pp") as f:
        lines = [ x for x in [line.strip() for line in f] if x != ""]
    for number, line in enumerate(lines):
        result = expression.parseString( line )
        print line, "->", result
     
