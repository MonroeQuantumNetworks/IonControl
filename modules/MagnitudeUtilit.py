# -*- coding: utf-8 -*-
"""
Created on Tue Jul 02 14:25:44 2013

@author: wolverine
"""

import modules.magnitude as magnitude
import math

def isMagnitude(value):
    return isinstance(value, magnitude.Magnitude)
    
def setSignificantDigits( mag_value, quantum ):
    """Sets the significant digits of a magnitude according the minimal step quantum
    and the current value
    >>> print setSignificantDigits(mg(1.23456789,'Hz'), mg(0.25,'Hz'))
    1.23 Hz
    >>> print setSignificantDigits(mg(0,'Hz'), mg(0.25,'Hz'))
    0 Hz
    >>> print setSignificantDigits(mg(-1.23456789,'Hz'), mg(0.25,'Hz'))
    -1.23 Hz
    
    """
    if mag_value.dimension()!=quantum.dimension():
        raise magnitude.MagnitudeError("setSignificantDigits needs matching dimensions {0} {1}".format(mag_value,quantum))
    digits = int(math.ceil(math.log(abs(mag_value/quantum),10))) if mag_value.toval()!=0 else 2
    mag_value.significantDigits = digits
    return mag_value

def createMagnitude( value, unit, quantum ):
    pass

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

def ensureCorrectUnit( unit, magnitudeVal ):
    """ensure unit is of the same dimension as the magnitude value,
    if yes, return unit, otherwise, return output unit of magnitudeVal"""
    try:
        if magnitude.mg(1,unit).dimension()==magnitudeVal.dimension():
            return unit
    except magnitude.MagnitudeError:
        pass
    return magnitudeVal.out_unit            
    
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
                    
if __name__ == '__main__':
    import doctest
    doctest.testmod()
    