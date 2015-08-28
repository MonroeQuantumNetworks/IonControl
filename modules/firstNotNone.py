'''
Created on Oct 20, 2014

@author: pmaunz
'''

def firstNotNone( *values ):
    """ Return the first argument in a list of arguments that is not None """
    for value in values:
        if value is not None:
            return value
    return None

