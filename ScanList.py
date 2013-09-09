# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
from modules import enum
import numpy
import random
import functools

ScanType = enum.enum('LinearUp', 'LinearDown', 'Randomized')

def shuffle( mylist ):
    random.shuffle(mylist)
    return mylist
    
    
def scanspace( start, stop, steps, scanSelect=0 ):
    if scanSelect==0:
        return numpy.linspace(start, stop, steps)
    else:
        mysteps = abs(steps) if stop>start else -abs(steps)
        return numpy.arange(start, stop+mysteps/2, mysteps)
        
def shuffled(start, stop, steps, scanSelect ):
    return shuffle(scanspace(start, stop, steps, scanSelect ))

def scanList( start, stop, steps, scantype=ScanType.LinearUp, scanSelect=0 ): 
    return { ScanType.LinearUp: functools.partial(scanspace, start, stop, steps, scanSelect ),
             ScanType.LinearDown: functools.partial(scanspace, stop, start, steps, scanSelect ),
             ScanType.Randomized: functools.partial(shuffled, stop, start, steps, scanSelect )
             }.get(scantype,functools.partial(scanspace, start, stop, steps, scanSelect ))()


if __name__ == "__main__":
    from magnitude import mg
    start = mg(12642,'MHz')
    stop = mg(12652,'MHz')
    steps = 11
    stepsmag = mg(500,'kHz')
    
    l = scanList( 0, 10 , -1, 1, 1)
    print "expected: [10 9 8 7 6 5 4 3 2 1 0] obtained", l
    print scanList( start, stop, stepsmag, 1, 1)
    print scanList( start, stop, steps)
    print scanList( start, stop, steps, ScanType.LinearDown)
    print scanList( start, stop, steps, ScanType.Randomized)
    print scanList( start, stop, stepsmag, ScanType.LinearUp, 1)
    
    print shuffle( [1,2,3] )
    print random.random()

    print scanList( mg(0), mg(360), mg(10) )