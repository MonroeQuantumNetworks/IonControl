# -*- coding: utf-8 -*-
"""
Created on Sat Feb 16 16:56:57 2013

@author: pmaunz
"""
from modules import enum
import numpy
import random

ScanType = enum.enum('LinearUp', 'LinearDown', 'Randomized')

def shuffle( mylist ):
    random.shuffle(mylist)
    return mylist
    

def scanList( start, stop, steps, scantype=ScanType.LinearUp ):
    
    return { ScanType.LinearUp: numpy.linspace(start, stop, steps),
             ScanType.LinearDown: numpy.linspace(stop, start, steps),
             ScanType.Randomized: shuffle(numpy.linspace(start,stop,steps))
             }.get(scantype,numpy.linspace(start, stop, steps))


if __name__ == "__main__":
    from magnitude import mg
    start = mg(12642,'MHz')
    stop = mg(12652,'MHz')
    steps = 11
    
    print scanList( start, stop, steps)
    print scanList( start, stop, steps, ScanType.LinearDown)
    print scanList( start, stop, steps, ScanType.Randomized)
    print scanList( start, stop, steps)
    
    print shuffle( [1,2,3] )
    print random.random()
