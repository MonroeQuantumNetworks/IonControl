# fourFn.py
#
# Demonstration of the pyparsing module, implementing a simple 4-function expression parser,
# with support for scientific notation, and symbols for e and pi.
# Extended to add exponentiation and simple built-in functions.
# Extended test cases, simplified pushFirst method.
#
# Copyright 2003-2006 by Paul McGuire
#
from pyparsing import Literal,CaselessLiteral,Word,Combine,Group,Optional,\
    ZeroOrMore,Forward,nums,alphas


point = Literal( "." )
e     = CaselessLiteral( "E" )
fnumber = Combine( Word( "+-"+nums, nums ) + 
                   Optional( point + Optional( Word( nums ) ) ) +
                   Optional( e + Word( "+-"+nums, nums ) ) )
ident = Word(alphas, alphas+nums+"_$")
funit = Combine( fnumber + Optional(Word(" "," ")) + ident )
 
plus  = Literal( "+" )
minus = Literal( "-" )
mult  = Literal( "*" )
div   = Literal( "/" )
lpar  = Literal( "(" ).suppress()
rpar  = Literal( ")" ).suppress()
addop  = plus | minus
multop = mult | div
expop = Literal( "^" )
pi    = CaselessLiteral( "PI" )


salutation     = Word( alphas + "'" )
comma          = Literal(",")
greetee        = Word( alphas )
endPunctuation = Literal("!")

greeting = salutation + comma + greetee + endPunctuation

tests = ("Hello, World!", 
"Hey, Jude!",
"Hi, Mom!",
"G'day, Mate!",
"Yo, Adrian!",
"Howdy, Pardner!",
"Whattup, Dude!" )

for t in tests:
        print t, "->", greeting.parseString(t)

 