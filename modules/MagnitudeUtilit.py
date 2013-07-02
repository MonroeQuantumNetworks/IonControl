# -*- coding: utf-8 -*-
"""
Created on Tue Jul 02 14:25:44 2013

@author: wolverine
"""

import magnitude

def value( obj, tounit=None ):
    """ return the value of a magnitude object, or float"""
    if not isinstance(obj, magnitude.Magnitude ):
        return obj
    if tounit:
        return obj.ounit(tounit).toval()
    return obj.toval()
    
def valueAs( obj, tounit=None ):
    """ return the value of a magnitude object, in the unit of another magnitude object"""
    if not isinstance(obj, magnitude.Magnitude ):
        return obj
    if tounit:
        if isinstance(tounit,magnitude.Magnitude ):
            return obj.ounit(tounit.out_unit).toval()
        else:
            return obj.ounit(tounit).toval()
    return obj.toval()    