# -*- coding: utf-8 -*-
"""
Created on Sun Feb 24 16:41:05 2013

@author: pmaunz
"""

from pyparsing import Literal,CaselessLiteral,Word,Combine,Optional,\
    nums,alphas, Suppress, ParseException,\
    SkipTo

import modules.magnitude as magnitude


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


expression = ( fnumber + Optional(ident)  )
precision = ( Suppress(SkipTo(point, include=True)) + Word( nums, nums ) )



if __name__=="__main__":
    for line in ['12MHz', '12.123456789 MHz','-200.234e34 us']:
        try:
            result = expression.parseString( line, parseAll=True )
            print line, "->", result
            print float(result[0]), result[1], magnitude.mg(float(result[0]),result[1])
            prec = precision.parseString( line )
            print len(prec[0])
        except ParseException as e:
            print "not a full match", e
     
