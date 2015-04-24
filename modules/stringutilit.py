# -*- coding: utf-8 -*-
"""
Created on Mon Mar 25 21:44:31 2013

@author: pmaunz
"""

def commentarize(text):
    return "# "+"\n# ".join(text.splitlines())

def stringToBool(s):
    return False if s in ['0','False','None'] else bool(s)