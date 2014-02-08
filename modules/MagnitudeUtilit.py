# -*- coding: utf-8 -*-
"""
Created on Tue Jul 02 14:25:44 2013

@author: wolverine
"""

import modules.magnitude as magnitude


def value( obj, tounit=None ):
    """ return the value of a magnitude object, or float"""
    if not isinstance(obj, magnitude.Magnitude ):
        return obj
    if tounit:
        return obj.ounit(tounit).toval()
    return obj.toval()
    
def haveSameDimension( first, second ):
    isFirstMag = isinstance( first, magnitude.Magnitude )
    isSecondMag = isinstance( second, magnitude.Magnitude )
    if isFirstMag and isSecondMag:
        return first.dimension()==second.dimension()
    elif isFirstMag:
        return first.dimensionless()
    elif isSecondMag:
        return second.dimensionless()
    return True
    
def valueAs( obj, tounit=None ):
    """ return the value of a magnitude object, in the unit of another magnitude object"""
    if not isinstance(obj, magnitude.Magnitude ):
        return obj
    if tounit:
        if isinstance(tounit,magnitude.Magnitude ):
            if tounit.out_unit:
                return obj.ounit( tounit.out_unit ).toval()
            else:
                return obj.toval()
        else:
            return obj.ounit(tounit).toval()
    return obj.toval()    
    
def mg( value, unit=None ):
    if isinstance(value, magnitude.Magnitude):
        return value
    if unit:
        return magnitude.mg(value,unit)
    return magnitude.mg(value)
    
_reverse_prefix = { -24: 'y',  # yocto
                    -21: 'z',  # zepto
                    -18: 'a',  # atto
                    -15: 'f',  # femto
                    -12: 'p',  # pico
                    -9: 'n',   # nano
                    -6: 'u',   # micro
                    -3: 'm',   # mili
                    -2: 'c',   # centi
                    -1: 'd',   # deci
                    3: 'k',    # kilo
                    6: 'M',    # mega
                    9: 'G',    # giga
                    12: 'T',   # tera
                    15: 'P',   # peta
                    18: 'E',   # exa
                    21: 'Z',   # zetta
                    24: 'Y'   # yotta
                    }
                    
#def reprefix(mag):
#    """change the prefix of the output unit of a magnitude
#    such that the value is between 1 and 1000
#    """
#    if mag.val == 0:
#        return mag
#    order = 3*int( math.floor( math.log10( abs(mag.val) )/3 ) )
    
    