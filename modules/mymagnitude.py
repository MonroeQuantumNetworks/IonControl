# -*- coding: utf-8 -*-
"""
Created on Wed Sep 18 20:33:29 2013

@author: pmaunz
"""

import magnitude
from round import roundToNDigits

class MagnitudeError(magnitude.MagnitudeError):
    pass

def reset_default_format():
    magnitude.reset_default_format()
    
def default_format(fmt=None):
    magnitude.default_format(fmt)
    
def output_units(un=None):
    magnitude.output_units(un)


class Magnitude(magnitude.Magnitude):
    def __init__(self, val, m=0, s=0, K=0, kg=0, A=0, mol=0, cd=0, dollar=0,b=0):
        magnitude.Magnitude.__init__(self,val,m,s,K,kg,A,mol,cd,dollar,b)
        self.significantDigits = 4    # if significant digits is not None, output will print this number of significant digits
        
    def __str__(self):
        if self.significantDigits:
            if self.out_unit:
                m = self.copy()
                m._div_by(self.out_factor)
                st = repr( roundToNDigits(m.val,self.significantDigits) )
                if magnitude._prn_units:
                    return st + ' ' + self.out_unit.strip()
                return st
    
            st = repr( roundToNDigits(m.val,self.significantDigits) )
            u = self.unit
            num = ' '  # numerator
            for i in range(len(magnitude._unames)):
                if u[i] == 1:
                    num = num + magnitude._unames[i] + ' '
                elif u[i] > 0:
                    num = num + magnitude._unames[i] + str(u[i]) + ' '
            den = ''  # denominator
            for i in range(len(magnitude._unames)):
                if u[i] == -1:
                    den = den + magnitude._unames[i] + ' '
                elif u[i] < 0:
                    den = den + magnitude._unames[i] + str(-u[i]) + ' '
            if den:
                if num == ' ':
                    num += '1 '
                st += (num + '/ ' + den)
            elif num != ' ':
                st += num        
            return st.strip()
        else:
            return magnitude.Magnitude.__str__(self)
        
        
        
                     
def mg(v, unit='', ounit=''):
    m = Magnitude(v)
    if unit:
        u = m.sunit2mag(unit)
        m._mult_by(u)
    if not ounit:
        ounit = unit
    m.ounit(ounit)
    return m
    
def ensmg(m, unit=''):
    if not isinstance(m, Magnitude):
        if type(m) == tuple:
            if len(m) == 2:
                return mg(m[0], m[1], unit)
            elif (len(m) == 1) and magnitude._numberp(m[0]):
                if unit:
                    return mg(m[0], unit)
                return Magnitude(m[0])
            else:
                raise MagnitudeError("Can't convert %s to Magnitude" %
                                     (m,))
        elif magnitude._numberp(m):
            if unit:
                return mg(m, unit)
            return Magnitude(m)
        else:
            raise MagnitudeError("Can't convert %s to Magnitude" %
                                 (m,))
    else:
        return m



if __name__=="__main__":
        a = mg(2,'kHz')
        print a
        a.significantDigits = 3
        print a        
        b = mg(2.3456789123,'m')
        print a
        a.significantDigits = 4
        print a
        print a*b