'''
Created on Oct 20, 2014

@author: pmaunz
'''

def firstNotNone( *values ):
    for value in values:
        if value is not None:
            return value
    return None
