'''
Created on Feb 21, 2014

@author: plmaunz
'''


def zeroCrossings( xarray, yarray, value=0 ):
    """return the x values of value crossings of the y values"""
    if len(xarray)<=2 and len(yarray)<=2:
        return None
    crossings = list()
    xiter, yiter = iter(xarray), iter(yarray)
    oldx , oldy = xiter.next(), yiter.next()
    for x, y in zip(xiter, yiter):
        if oldy<value != y<value:
            crossings.append( (x*oldy - oldx*y)/(oldy-y) )
    return crossings
        