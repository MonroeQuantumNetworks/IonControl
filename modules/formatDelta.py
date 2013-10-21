# -*- coding: utf-8 -*-
"""
Created on Fri Oct 11 14:34:28 2013

@author: wolverine
"""

def formatDelta(delta):
    """Return a string version of a datetime time difference object (timedelta),
       formatted as: HH:MM:SS.S. If hours = 0, returns MM:SS.S"""
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    hours = hours + delta.days*24
    seconds = seconds + delta.microseconds*1e-6
    components = list()
    if (hours > 0): components.append("{0}".format(hours))
    components.append("{0:02d}:{1:04.1f}".format(int(minutes),seconds))
    return ":".join(components)