'''
Created on May 16, 2015

@author: pmaunz
'''

def dictValueFind( dd, value ):
    try:
        return (key for key,v in dd.items() if v==value).next()
    except StopIteration:
        return None