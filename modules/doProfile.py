'''
Created on Feb 7, 2014

@author: pmaunz
'''
import cProfile
import pstats


def doprofile(func):
    def profiled_func(*args, **kwargs):
        profile = cProfile.Profile()
        try:
            profile.enable()
            result = func(*args, **kwargs)
            profile.disable()
            return result
        finally:
            sortby = 'cumulative'
            ps = pstats.Stats(profile).sort_stats(sortby)            
            ps.print_stats()
    return profiled_func

