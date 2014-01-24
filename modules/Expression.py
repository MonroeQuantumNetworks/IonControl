# fourFn.py
#
# Demonstration of the pyparsing module, implementing a simple 4-function expression parser,
# with support for scientific notation, and symbols for e and pi.
# Extended to add exponentiation and simple built-in functions.
# Extended test cases, simplified pushFirst method.
#
# Copyright 2003-2006 by Paul McGuire
#
import magnitude as magnitude
from pyparsing import Literal,CaselessLiteral,Word,Combine,Optional,\
    ZeroOrMore,Forward,nums,alphas
import math
import operator

point = Literal( "." )
e     = CaselessLiteral( "E" )
plus  = Literal( "+" )
minus = Literal( "-" )
dotNumber = Combine( Optional(plus | minus) + point + Word(nums)+
                   Optional( e + Word( "+-"+nums, nums ) ) )
numfnumber = Combine( Word( "+-"+nums, nums ) + 
                   Optional( point + Optional( Word( nums ) ) ) +
                   Optional( e + Word( "+-"+nums, nums ) ) )
fnumber = numfnumber | dotNumber
ident = Word(alphas, alphas+nums+"_$")
funit = Combine( fnumber + Optional(Word(" "," ")) + ident )
 
mult  = Literal( "*" )
div   = Literal( "/" )
lpar  = Literal( "(" ).suppress()
rpar  = Literal( ")" ).suppress()
addop  = plus | minus
multop = mult | div
expop = Literal( "^" )
pi    = CaselessLiteral( "PI" )


def sqrt( value ):
    if isinstance( value, magnitude.Magnitude ):
        return value.sqrt()
    return math.sqrt(value)
    
def myround( value ):
    if isinstance( value, magnitude.Magnitude ):
        return value.round()
    return round(value)

epsilon = 1e-12
opn = { "+" : operator.add,
        "-" : operator.sub,
        "*" : operator.mul,
        "/" : operator.div,
        "^" : operator.pow }
fn  = { "sin" : math.sin,
        "cos" : math.cos,
        "tan" : math.tan,
        "log" : math.log,
        "acos" : math.acos,
        "asin" : math.asin,
        "atan" : math.atan,
        "degrees" : math.degrees,
        "radians" : math.radians,
        "erf" : math.erf,
        "erfc" : math.erfc,
        "abs" : abs,
        "exp" : math.exp,
        "trunc" : lambda a: int(a),
        "round" : myround,
        "sgn" : lambda a: abs(a)>epsilon and cmp(a,0) or 0,
        "sqrt" : sqrt }


class Expression:
    exprStack = []

    def __init__(self, variabledict=dict()):
        variabledict.setdefault('pi',math.pi)
        variabledict.setdefault('e',math.e)
        """
        expop   :: '^'
        multop  :: '*' | '/'
        addop   :: '+' | '-'
        integer :: ['+' | '-'] '0'..'9'+
        atom    :: PI | E | real | fn '(' expr ')' | '(' expr ')'
        factor  :: atom [ expop factor ]*
        term    :: factor [ multop factor ]*
        expr    :: term [ addop term ]*
        """
        expr = Forward()
        atom = (Optional("-") + ( funit | fnumber | ident + lpar + expr + rpar | ident ).setParseAction( self.pushFirst ) | ( lpar + expr.suppress() + rpar )).setParseAction(self.pushUMinus) 
        
        # by defining exponentiation as "atom [ ^ factor ]..." instead of "atom [ ^ atom ]...", we get right-to-left exponents, instead of left-to-righ
        # that is, 2^3^2 = 2^(3^2), not (2^3)^2.
        factor = Forward()
        factor << atom + ZeroOrMore( ( expop + factor ).setParseAction( self.pushFirst ) )
        
        term = factor + ZeroOrMore( ( multop + factor ).setParseAction( self.pushFirst ) )
        expr << term + ZeroOrMore( ( addop + term ).setParseAction( self.pushFirst ) )
        self.bnf = expr
        self.variabledict = variabledict
        self.funit = fnumber + ZeroOrMore(ident)


    def pushFirst(self, strg, loc, toks ):
        self.exprStack.append( toks[0] )
        
    def pushUMinus(self, strg, loc, toks ):
        if toks and toks[0]=='-': 
            self.exprStack.append( 'unary -' )
            #~ exprStack.append( '-1' )
            #~ exprStack.append( '*' )

    # map operator symbols to corresponding arithmetic operations
    def evaluateStack(self, s, dependencies ):
        op = s.pop()
        if op == 'unary -':
            return -self.evaluateStack( s, dependencies )
        if op in "+-*/^":
            op2 = self.evaluateStack( s, dependencies )
            op1 = self.evaluateStack( s, dependencies )
            return opn[op]( op1, op2 )
        elif op == "PI" or op=='pi':
            return math.pi # 3.1415926535
        elif op == "E":
            return math.e  # 2.718281828
        elif op in fn:
            return fn[op]( self.evaluateStack( s, dependencies ) )
        elif op in self.variabledict:
            dependencies.add(op)
            return self.variabledict[op]
        elif op[0].isalpha():
            return 0
        else:
    #        return float(op)
            try:
                res = float(op)
                #res = magnitude.mg(res)
            except ValueError: # lets try whether it has a unit
                fmag = Optional(fnumber).setResultsName('num') + Optional(ident).setResultsName('unit')
                l = fmag.parseString(op)
                m = magnitude.mg( float(l.get('num',1)), l.get('unit', '') )
                m.significantDigits = len(list(filter( lambda s: s.isdigit(), l.get('num','1') )))
                return m
            return res
            
    def evaluate(self, expression, variabledict=dict(), listDependencies=False ):
        self.variabledict = variabledict
        self.exprStack = []
        self.results = self.bnf.parseString(expression)
        dependencies = set()
        value = self.evaluateStack( self.exprStack[:], dependencies )
        if listDependencies:
            return value, dependencies
        return value
        
    def evaluateAsMagnitude(self, expression, variabledict=dict()):
        res = self.evaluate(expression, variabledict)
        if not isinstance(res, magnitude.Magnitude ):
            res = magnitude.mg( res )
        return res

if __name__ == "__main__":
    
    ExprEval = Expression()
    
    def test( s, expVal, variabledict=dict() ):
        val = ExprEval.evaluate( s, variabledict )
        if val == expVal:
            print s, "=", val, ExprEval.results, "=>", ExprEval.exprStack
        else:
            print s+"!!!", val, "!=", expVal, ExprEval.results, "=>", ExprEval.exprStack
  
    test( "9", 9 )
    test( "-9", -9 )
    test( "--9", 9 )
    test( "-E", -math.e )
    test( "9 + 3 + 6", 9 + 3 + 6 )
    test( "9 + 3 / 11", 9 + 3.0 / 11 )
    test( "(9 + 3)", (9 + 3) )
    test( "(9+3) / 11", (9+3.0) / 11 )
    test( "9 - 12 - 6", 9 - 12 - 6 )
    test( "9 - (12 - 6)", 9 - (12 - 6) )
    test( "2*3.14159", 2*3.14159 )
    test( "3.1415926535*3.1415926535 / 10", 3.1415926535*3.1415926535 / 10 )
    test( "PI * PI / 10", math.pi * math.pi / 10 )
    test( "PI*PI/10", math.pi*math.pi/10 )
    test( "PI^2", math.pi**2 )
    test( "round(PI^2)", round(math.pi**2) )
    test( "6.02E23 * 8.048", 6.02E23 * 8.048 )
    test( "e / 3", math.e / 3 )
    test( "sin(pi/2)", math.sin(math.pi/2) )
    test( "trunc(E)", int(math.e) )
    test( "trunc(-E)", int(-math.e) )
    test( "round(E)", round(math.e) )
    test( "round(-E)", round(-math.e) )
    test( "E^PI", math.e**math.pi )
    test( "2^3^2", 2**3**2 )
    test( "2^3+2", 2**3+2 )
    test( "2^9", 2**9 )
    test( ".5", 0.5)
    test( "-.7", -0.7)
    test( "-.7ms", magnitude.mg(-0.7,"ms"))
    test( "sgn(-2)", -1 )
    test( "sgn(0)", 0 )
    test( "sgn(0.1)", 1 )
    test( "2*(3+5)", 16 )
    test( "2*(alpha+beta)", 14, {'alpha':5,'beta':2} )
    test( "-4 MHz" , magnitude.mg(-4,'MHz') )
    test( "2*4 MHz" , magnitude.mg(8,'MHz') )
    test( "2 * sqrt ( 4s / 1 s)",4 )
    test( "sqrt( 4s*4s )",magnitude.mg(4,'s'))
    test( "piTime",magnitude.mg(10,'ms'),{'piTime':magnitude.mg(10,'ms')} )

    print ExprEval.evaluate( "4 MHz" )
