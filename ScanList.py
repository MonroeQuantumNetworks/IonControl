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
    
    
def scanspace( start, stop, steps, scanSelect=0 ):
    if scanSelect==0:
        return numpy.linspace(start, stop, steps)
    else:
        return numpy.arange(start, stop+steps/2, steps)

def scanList( start, stop, steps, scantype=ScanType.LinearUp, scanSelect=0 ):
    
    return { ScanType.LinearUp: scanspace(start, stop, steps, scanSelect ),
             ScanType.LinearDown: scanspace(start, stop, steps, scanSelect ),
             ScanType.Randomized: shuffle(scanspace(start, stop, steps, scanSelect ))
             }.get(scantype,scanspace(start, stop, steps, scanSelect ))


if __name__ == "__main__":
    from magnitude import mg
    start = mg(12642,'MHz')
    stop = mg(12652,'MHz')
    steps = 11
    stepsmag = mg(500,'kHz')
    
    print scanList( start, stop, steps)
    print scanList( start, stop, steps, ScanType.LinearDown)
    print scanList( start, stop, steps, ScanType.Randomized)
    print scanList( start, stop, stepsmag, ScanType.LinearUp, 1)
    
    print shuffle( [1,2,3] )
    print random.random()

    print scanList( mg(0), mg(360), mg(10) )