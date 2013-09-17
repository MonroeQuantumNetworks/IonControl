# -*- coding: utf-8 -*-
"""
Created on Sat Sep 14 07:50:05 2013

@author: pmaunz
"""
import math

def roundToNDigits(value,n):
    """round value to n significant digits
    """
    if value==None or math.isNan(value) or math.isinf(value):
        return value
    if abs(value)==0:
        return 0
    if not n:
        n=0
    return round( value,  -int(math.floor(math.log10(abs(value) ))) + (n - 1))   
    
def roundToStdDev(value, stddev, extradigits=0):
    """round value to the significant digits determined by the stddev
    and add extradigits nonsignificant digits
    """
    if value==None:
        return None
    if abs(value)==0:
        return 0
    if not stddev:
        stddev=0
    return roundToNDigits( value, int(math.log10(math.ceil(abs(value)/stddev)-0.5)+2+extradigits) if stddev>0 else 3)


if __name__=="__main__":
    print roundToNDigits( -123.45, 2 )
    print roundToNDigits( 12.45, 2 )
    print roundToNDigits( -1.45, 2 )
    print roundToNDigits( 0.45, 2 )
    print roundToNDigits( 0.045, 2 )
    print roundToNDigits( 0.0045, 2 )
    
    print roundToStdDev( 5.123445, 2 )
    print roundToStdDev( 5.123445, 1 )
    print roundToStdDev( 5.123445, 0.1 )
    print roundToStdDev( 5.123445, 0.01 )
    print roundToStdDev( 5.123445, 0.001 )
    
    print roundToNDigits(None,1)
    print roundToNDigits(None,None)
    print roundToNDigits(1,None)
    
    