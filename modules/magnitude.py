# magnitude  -- a module for computing with numbers with units.
#
# Version 0.9.5, June 2013
#
# Copyright (C) 2006-2013 Juan Reyero (http://juanreyero.com).
#
# Licensed under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied.  See the License for the specific
# language governing permissions and limitations under the
# License.
#
# Home page: http://juanreyero.com/open/magnitude/
#
# Extended by Peter Maunz, Sandia National Laboratories, 2013
#

"""
A physical quantity is a number with a unit, like 10 km/h. Units can be any
of the SI units, plus a bunch of non-SI, bits, dollars, and any combination
of them. They can include the standard SI prefixes. Magnitude can operate
with physical quantities, parse their units, and print them. You don't have
to worry about unit consistency or conversions; everything is handled
transparently. By default output is done in basic SI units, but you can
specify any output unit, as long as it can be reduced to the basic units of
the physical quantity.

The basic units understood by the magnitude module are:

    indicator    meaning
    ---------    -------
    $            dollar ('dollar' is also acceptable)
    A            ampere
    b            bit
    cd           candela
    K            degrees Kelvin
    kg           kilograms
    m            meters
    mol          amount of substance
    s            seconds

From these basic units you can derive many other units.  The magnitude
package predefines these derived units:

    Bq           becquerel
    C            coulomb
    c            speed of light (m/s)
    day
    degC         degree Celsius
    dpi          dots per inch
    F            farad
    ft           feet ("'" is also acceptable)
    g            gram
    gravity      acceleration due to gravity (m/s**2)
    Gy           gray
    H            henry
    h            hour
    Hz           Hertz
    inch         ('"' is also acceptable)
    ips          inches per second
    J            joule
    kat          katal
    l            liter
    lightyear    light year
    lm           lumen
    lpi          lines per inch
    lux
    min          minute
    N            newton
    ohm
    Pa           pascal
    S            siemens
    Sv           sievert
    T            tesla
    V            volt
    W            watt
    Wb           weber
    year
    B            byte

Two magnitudes have no units, 'rad' (radian - unit of plane angle) and 'sr'
(steradian - unit of solid angle).

Any of the above units can be augmented with the following set of scale
prefixes:

    letter     scale    name
    ------     -----    ----
    y          1e-24    yocto
    z          1e-21    zepto
    a          1e-18    atto
    f          1e-15    femto
    p          1e-12    pico
    n          1e-9     nano
    u          1e-6     micro
    m          1e-3     mili
    c          1e-2     centi
    d          1e-1     deci
    k          1e3      kilo
    Ki         2^10     Kibi
    M          1e6      mega
    Mi         2^20     Mebi
    G          1e9      giga
    Gi         2^30     Gibi
    T          1e12     tera
    Ti         2^40     Tebi
    P          1e15     peta
    Pi         2^50     Pebi
    E          1e18     exa
    Ei         2^60     Exbi
    Z          1e21     zetta
    Y          1e24     yotta

Exported symbols
----------------

- Magnitude [class] --- Numbers with units; math operations are overloaded
- mg(number, unit, ounit='') --- Construct a Magnitude
- ensmg(m, unit='') --- Tries to build a Magnitude out of something
- newmag(indicator, mag) --- Intern a new magnitude with its name
- MagnitudeError [class] --- Magnitude error handling


Defining new magnitudes
-----------------------

You can define new magnitudes by instantiating the Magnitude class.  Suppose
you want to define pounds as a magnitude and associate with it the unit
'lb'.  A pound is 0.45359237 kilograms, so we have

    >>> lb = Magnitude(0.45359237, kg=1)

To make it recognized automatically you also have to introduce it to
the system:

    >>> new_mag('lb', lb)

You can then use it as you would any other predefined physical quantity:

    >>> me = mg(180, 'lb')
    >>> print me.ounit('kg').toval()
    81.6466266

The following online references provide more detail about physical units and
the SI system.

    http://physics.nist.gov/cuu/Units/units.html
    http://en.wikipedia.org/wiki/SI
    http://www.gnu.org/software/units/units.html for units.dat
    http://www.cip.physik.uni-muenchen.de/~tf/misc/etools.lisp

This code was very much inspired by
    http://www.cs.utexas.edu/users/novak/units.html
and its associated paper,
    http://www.cs.utexas.edu/users/novak/units95.html


Bits and bytes (2009-11-03)
---------------------------

A previous version of the library used "bit" for bit and "b" for byte,
leaving B for Bel.  Following Michael Scheper's suggestion we follow
now IEEE 1541 and use "b" for bit and "B" for byte.  If the need
arises I'll implement ad-hoc esupport for dB, but for the time being
there is none.
"""

import re, math
import types

class Enumerate(dict):
    """C enum emulation (original by Scott David Daniels)"""
    def __init__(self, names):
        for number, name in enumerate(names.split()):
            setattr(self, name, number)
            self[number] = name


# Base magnitude names and prefixes.  The _mags dictionary, initialized
# at the end, will contain all the known magnitudes.  Units are
# 9-element arrays, each element the exponent of the unit named by the
# Uname in the same position.
class MagnitudeError(Exception):
    pass

_mags = {}
_outputDimensions = {}
_unames = ['m', 's', 'K', 'kg', 'A', 'mol', 'cd', '$', 'b']
_prefix = {'y': 1e-24,  # yocto
           'z': 1e-21,  # zepto
           'a': 1e-18,  # atto
           'f': 1e-15,  # femto
           'p': 1e-12,  # pico
           'n': 1e-9,   # nano
           'u': 1e-6,   # micro
           'm': 1e-3,   # mili
           'c': 1e-2,   # centi
           'd': 1e-1,   # deci
           'k': 1e3,    # kilo
           'M': 1e6,    # mega
           'G': 1e9,    # giga
           'T': 1e12,   # tera
           'P': 1e15,   # peta
           'E': 1e18,   # exa
           'Z': 1e21,   # zetta
           'Y': 1e24,   # yotta

           # Binary prefixes, approved by the International
           # Electrotechnical Comission in 1998.  Since then, kb means
           # 1000 bytes; for 1024 bytes use Kib (note the capital K in
           # the binary version, and the lower case for the b of byte,
           # see comment in byte definition below).
           'Ki': 2 ** 10, # Kibi (<- kilo, 10^3)
           'Mi': 2 ** 20, # Mebi (<- mega, 10^6)
           'Gi': 2 ** 30, # Gibi (<- giga, 10^9)
           'Ti': 2 ** 40, # Tebi (<- tera, 10^12)
           'Pi': 2 ** 50, # Pebi (<- peta, 10^15)
           'Ei': 2 ** 60  # Exbi (<- exa, 10^18)
           }
_reverse_prefix = { -24: 'y',  # yocto
                    -21: 'z',  # zepto
                    -18: 'a',  # atto
                    -15: 'f',  # femto
                    -12: 'p',  # pico
                    -9: 'n',   # nano
                    -6: 'u',   # micro
                    -3: 'm',   # mili
                    -2: 'c',   # centi
                    -1: 'd',   # deci
                    0: '',
                    3: 'k',    # kilo
                    6: 'M',    # mega
                    9: 'G',    # giga
                    12: 'T',   # tera
                    15: 'P',   # peta
                    18: 'E',   # exa
                    21: 'Z',   # zetta
                    24: 'Y'   # yotta
                    }


###### Default print formatting options

_default_prn_format = "%.*f"
_prn_format = _default_prn_format
_prn_prec = 4
_prn_units = True

def reset_default_format():
    """Resets the default output format.

    By default the output format is "%.*f", where * gets replaced by
    the output precision.
    """
    global _prn_format
    _prn_format = _default_prn_format

def default_format(fmt=None):
    """Get or set the default ouptut format.

    Include a fmt if and where you need to specify the output
    precision.  Defaults to %.*f, where the * stands for the
    precision.  Do nothing if fmt is None.

    Returns: default format.

    >>> print mg(2, 'm2').sqrt()
    1.4142 m
    >>> default_format("%.2f")
    '%.2f'
    >>> print mg(2, 'm2').sqrt()
    1.41 m
    >>> reset_default_format()
    """
    global _prn_format
    if fmt is not None:
        _prn_format = fmt
    return _prn_format

def output_precision(prec=None):
    """Get or set the output precision.

    Package default is 4.  Do nothing is prec is None.

    Returns: default precision.

    >>> default_format("%.*f")
    '%.*f'
    >>> print mg(2, 'm2').sqrt()
    1.4142 m
    >>> output_precision(6)
    6
    >>> print mg(2, 'm2').sqrt()
    1.414214 m
    >>> output_precision(4)
    4
    """
    global _prn_prec
    if prec is not None:
        _prn_prec = prec
    return _prn_prec

def output_units(un=None):
    """Enable or disable the output of units when printing.

    By default output of units is enabled.  Do nothing if un is None.
    When disabled (un is False) print of Magnitudes will produce only
    numbers.

    Return: True if output of units enabled, False otherwise.

    >>> print mg(2, 'day')
    2.0000 day
    >>> output_units(False)
    False
    >>> print mg(2, 'day').ounit('s')
    172800.0000
    """
    global _prn_units
    if un is not None:
        _prn_units = un
    return _prn_units


###### Resolution areas

def _res2num(res):
    match = re.search(r'(\d+)x(\d+)', res)
    if match:
        return int(match.group(1)), int(match.group(2))
    if (res[0] == '[') and (res[-1] == ']'):
        return (int(res[1:-1]), int(res[1:-1]))

def _isres(res):
    return (len(res) > 2) and (res[0] == '[') and (res[-1] == ']')

def _res2m2(res):
    """Convert resolution string to square meters.

    Bracketed resolutions are used in the printing industry, to
    denote the area of a pixel.  Can be like [300x1200] or like [600]
    (=[600x600]), meaning the area of square pixels of size 1"/300 x
    1"/1200 and 1"/600 x 1"/600.  The square brackes are intended to
    show that we are talking about areas.  This function converts them
    to square meters.

    >>> _res2m2("[600x600]")
    1.792111111111111e-09
    >>> _res2m2("[600]")
    1.792111111111111e-09
    >>> _res2m2("[150x300]")
    1.4336888888888889e-08
    """
    hr, vr = _res2num(res)
    return 0.0254 * 0.0254 / (vr * hr)


def roundToNDigits(value,n):
    """round value to n significant digits
    """
    if value is None or math.isnan(value) or math.isinf(value) or value==0:
        return value
    if not n:
        n=0
    return round( value,  -int(math.floor(math.log10(abs(value) ))) + (n - 1))

def digitsToPrecision(value, n):
    """convert the number of significant digits into the precision (number of digits after the period"""
    if value is None or math.isnan(value) or math.isinf(value) or value==0:
        return 0
    return max(0, -int(math.floor(math.log10(abs(value) ))) + (n - 1) )

# Definition of the magnitude type.  Includes operator overloads.

def _numberp(n):  ## Python has to have a decent way to do this!
    return (isinstance(n, types.ComplexType) or
            isinstance(n, types.FloatType) or
            isinstance(n, types.IntType) or
            isinstance(n, types.LongType))

class Magnitude():
    Format = Enumerate("precision significantDigits")
    def __init__(self, val, m=0, s=0, K=0, kg=0, A=0, mol=0, cd=0, dollar=0,
                 b=0):
        self.val = val
        self.unit = [m, s, K, kg, A, mol, cd, dollar, b]
        self.out_unit = None
        self.out_factor = None
        self.oprec = None
        self.oformat = None
        self.significantDigits = None
        self.strFormat = self.Format.significantDigits

    def copy_format(self, other):
        """ copy the formatting options form other to self
        self and other need to have the same unit
        
        >>> a = mg(123.345, 'MHz')
        >>> a.significantDigits = 6
        >>> print a
        123.345 MHz
        >>> b = mg( 1.23456789, 'GHz' )
        >>> b.copy_format( a )
        >>> print b
        1234.57 MHz
        """
        if other.unit != self.unit:
            raise MagnitudeError("Incompatible units: %s and %s" %
                                 (other.unit, self.unit))
        self.out_unit = other.out_unit
        self.out_factor = other.out_factor
        self.oprec = other.oprec
        self.oformat = other.oformat
        self.significantDigits = other.significantDigits
        self.strFormat = other.strFormat
        
    def update_value(self, value, unitstr ):
        """ update value and unit, leave formatting as is
        
        >>> a = mg(123.345, 'MHz')
        >>> a.significantDigits = 6
        >>> print a
        123.345 MHz
        >>> a.update_value( 0.234, 'GHz' )
        >>> print a
        234.0 MHz
        >>> a.update_value( 234567.89, 'kHz' )
        >>> print a
        234.568 MHz
        """
        newval = mg(value, unitstr)
        if newval.unit != self.unit:
            raise MagnitudeError("Incompatible units: %s and %s" %
                                 (newval.unit, self.unit))
        self.val = newval.val        

    def copysign(self, other):
        """ copy the sign from other
        
        >>> a = mg(-123, 'kHz')
        >>> b = mg(250, 'kHz')
        >>> print b
        250.0000 kHz
        >>> c = b.copysign(a)
        >>> print c
        -250.0000 kHz
        """
        r = self.copy(True)
        r.val = math.copysign( self.val, other.val )
        return r

    def __setstate__(self, state):
        """this function ensures that the given fields are present in the class object
        after unpickling. Only new class attributes need to be added here.
        """
        self.__dict__ = state
        self.__dict__.setdefault( 'strFormat' , self.Format.significantDigits )

    def __copy__(self):
        """Builds and returns a copy of a magnitude.

        The copy includes value and units.  If with_format is set to
        True the default output unit, output factor, output precision
        and output format are also copied.

        >>> a = mg(1000/3., 'mm')
        >>> print a.output_prec(2)
        333.33 mm
        >>> print a.copy()
        333.3333 mm
        >>> print a.copy(with_format=True)
        333.33 mm
        """
        cp = Magnitude(self.val, *self.unit)
        cp.out_unit = self.out_unit
        cp.out_factor = self.out_factor
        cp.oprec = self.oprec
        cp.oformat = self.oformat
        cp.strFormat = self.strFormat
        cp.significantDigits = self.significantDigits
        return cp

    def copy(self, with_format=True):
        """Builds and returns a copy of a magnitude.

        The copy includes value and units.  If with_format is set to
        True the default output unit, output factor, output precision
        and output format are also copied.

        >>> a = mg(1000/3., 'mm')
        >>> print a.output_prec(2)
        333.33 mm
        >>> print a.copy()
        333.3333 mm
        >>> print a.copy(with_format=True)
        333.33 mm
        """
        cp = Magnitude(self.val, *self.unit)
        if with_format:
            cp.out_unit = self.out_unit
            cp.out_factor = self.out_factor
            cp.oprec = self.oprec
            cp.oformat = self.oformat
            cp.strFormat = self.strFormat
        cp.significantDigits = self.significantDigits
        return cp

    def toval(self, ounit=''):
        """Returns the numeric value of a magnitude.

        The value is given in ounit or in the Magnitude's default
        output unit.

        >>> v = mg(100, 'km/h')
        >>> v.toval()
        100.0
        >>> v.toval(ounit='m/s')
        27.77777777777778
        """
        m = self.copy()
        if not ounit:
            ounit = self.out_unit
        if ounit:
            out_factor = self.sunit2mag(ounit)
            m._div_by(out_factor)
        return m.val

    def _unitRepr_(self):
        u = self.unit
        num = ' '  # numerator
        for i in range(len(_unames)):
            if u[i] == 1:
                num = num + _unames[i] + ' '
            elif u[i] > 0:
                num = num + _unames[i] + str(u[i]) + ' '
        den = ''  # denominator
        for i in range(len(_unames)):
            if u[i] == -1:
                den = den + _unames[i] + ' '
            elif u[i] < 0:
                den = den + _unames[i] + str(-u[i]) + ' '
        st = ''
        if den:
            if num == ' ':
                num += '1 '
            st += (num + '/ ' + den)
        elif num != ' ':
            st += num
        return st

    def _formatNumber_(self, strFormat ):
        strFormat = self.strFormat if strFormat is None else strFormat
        if self.significantDigits and strFormat==self.Format.significantDigits:
            #st = repr( roundToNDigits(self.val,self.significantDigits) )
            st = "{{0:.{0}f}}".format( digitsToPrecision(self.val, self.significantDigits)).format( roundToNDigits(self.val,self.significantDigits) )
        else:
            oformat = self.oformat if self.oformat is not None else _prn_format
            oprec = self.oprec if self.oprec is not None else _prn_prec
            if '*' in oformat:  # requires the precision arg
                st = oformat % (oprec, self.val)
            else:
                st = oformat % (self.val)
        return st     

    def _bestPrefix_(self):
        r = math.log10(abs(self.val))/3 if self.val != 0 else 0
        r2 = math.floor(r)
        r3 = math.copysign(r2,r)*3
        r4 = int(r3) if not( math.isnan(r3) or math.isinf(r3) ) else 0
        return _reverse_prefix[r4]               

    def __str__(self):
        if _prn_units:
            return " ".join( self.toStringTuple() )
        return self.toStringTuple()[0]  
    
    def toString(self, strFormat=None ):
        if _prn_units:
            return " ".join( self.toStringTuple(strFormat) )
        return self.toStringTuple( strFormat )[0]  
              
    def suggestedUnit(self):
        if self.out_unit:
            return self.out_unit
        outmag = _mags[_outputDimensions[tuple(self.unit)]]
        m = self.copy(True)
        m._div_by(outmag)
        prefix = m._bestPrefix_()
        return prefix+_outputDimensions[tuple(self.unit)]       
    
    def toStringTuple(self, strFormat=None ):
        unitTuple = tuple(self.unit)
        if math.isinf(self.val) or math.isnan(self.val):
            return (str(self.val),"")
        if self.out_unit:
            m = self.copy(True)
            m._div_by(self.out_factor)
            return ( m._formatNumber_( strFormat ).strip(), self.out_unit.strip() )
        elif unitTuple in _outputDimensions:
            outmag = _mags[_outputDimensions[unitTuple]]
            m = self.copy(True)
            m._div_by(outmag)
            prefix = m._bestPrefix_()
            if prefix != '':
                m = self.copy(True)
                outmag = self.sunit2mag( prefix+_outputDimensions[unitTuple] )
                m._div_by(outmag)
            return ( m._formatNumber_( strFormat ).strip(), (prefix + _outputDimensions[unitTuple]).strip() )
        else:
            return ( self._formatNumber_( strFormat ).strip(), self._unitRepr_().strip() )

    def term2mag(self, s):
        """Converts a string with units to a Magnitude.

        Can't divide: use with the numerator and the denominator
        separately (hence the "term").  Returns the Magnitude that the
        string represents.  Units are separated by spaces, powers are
        integers following the unit name.

        Cannot parse fractional units.  Cannot parse multi-digit
        exponents.

        >>> a = mg(1, '')
        >>> print a.term2mag('V2  A')
        1.0000 m4 kg2 / s6 A
        >>> print a.term2mag('kft year') # kilo-feet year
        9618551037.0820 m s
        """
        m = Magnitude(1.0)
        units = re.split(r'\s', s)
        for u in units:
            if re.search(r'[^\s]', u):
                exp = 1
                if re.search(r'\d$', u):
                    exp = int(u[-1])
                    u = u[0:-1]
                if _mags.has_key(u):
                    u = _mags[u].copy()
                elif ((len(u)>=3) and _prefix.has_key(u[0:2]) and
                      _mags.has_key(u[2:])):
                    pr = _prefix[u[0:2]]
                    u = _mags[u[2:]].copy();  u.val = pr * u.val
                elif ((len(u)>=2) and _prefix.has_key(u[0]) and
                      _mags.has_key(u[1:])):
                    pr = _prefix[u[0]]
                    u = _mags[u[1:]].copy();  u.val = pr * u.val
                elif _isres(u):
                    u = Magnitude(_res2m2(u), m=2)
                elif u == '':
                    u = Magnitude(1.0)
                else:
                    raise MagnitudeError("Don't know about unit %s" % u)
                for _ in range(exp):
                    m._mult_by(u)
        return m

    def sunit2mag(self, unit=''):
        """Convert a units string to a Magnitude.

        Uses term2mag to convert a string with units, possibly
        including a / to separate a numerator and a denominator, to a
        Magnitude.

        >>> a = mg(1, '')
        >>> a.sunit2mag('m/s').toval()
        1.0
        >>> a.sunit2mag('km/h').toval()
        0.2777777777777778
        >>> print a.sunit2mag('W h')
        3.6000 kJ
        >>> print a.sunit2mag('W h').ounit('J')
        3600.0000 J
        >>> print a.sunit2mag('m2 kg / s3 Pa')
        1.0000 m3 / s
        >>> print a.sunit2mag('m2 kg/s3').ounit('W')
        1.0000 W
        """
        m = Magnitude(1.0)
        if unit:
            q = re.split(r'/', unit)
            if re.search(r'[^\s]', q[0]):
                m._mult_by(self.term2mag(q[0]))
            if (len(q) == 2) and re.search(r'[^\s]', q[1]):
                m._div_by(self.term2mag(q[1]))
        return m

    def dimensionless(self):
        """True if the magnitude's dimension exponents are all zero.

        >>> mg(2, 'K').dimensionless()
        False
        >>> mg(2, 'rad').dimensionless()
        True
        """
        return self.unit == [0] * 9

    def dimension(self):
        """Return the dimension of the unit in internal (array) format.

        >>> mg(2, 'J').dimension()
        [2, -2, 0, 1, 0, 0, 0, 0, 0]
        """
        return self.unit[:]

    def has_dimension(self, u):
        """Returns true if the dimension of the magnitude matches u:

        >>> s = mg(120, 'km/h') * (2, 'day')
        >>> s.has_dimension('m')
        True
        >>> print s.ounit('cm')
        576000000.0000 cm
        """
        o = self.sunit2mag(u)
        return (self.unit == o.unit)

    def _mult_by(self, m):
        self.val *= m.val
        for i in range(len(self.unit)):
            self.unit[i] = self.unit[i] + m.unit[i]
        self.out_unit = None
        self.significantDigits = max( self.significantDigits, 1) + max(m.significantDigits,1 )

    def _div_by(self, m):
        self.val /= m.val
        for i in range(len(self.unit)):
            self.unit[i] = self.unit[i] - m.unit[i]
        self.out_unit = None
        self.significantDigits = max( self.significantDigits, m.significantDigits )

    def ounit(self, unit):
        """Set the preferred unit for output, returning the Magnitude.

        >>> a = mg(1, 'kg m2 / s2')
        >>> print a
        1.0000 kg m2 / s2
        >>> print a.ounit('J')
        1.0000 J
        >>> print a
        1.0000 J
        """
        self.out_unit = unit
        self.out_factor = self.sunit2mag(unit)
        if self.out_factor.unit != self.unit:
            raise MagnitudeError("Inconsistent Magnitude units: %s, %s" %
                                (self.out_factor.unit, self.unit))
        return self

    def to_base_units(self):
        """Forgets about the output unit and goes back to base units:

        >>> a = mg(10, 'km')
        >>> print a
        10.0000 km
        >>> print a.to_base_units()
        10.0000 km
        """
        self.out_unit = None
        self.out_factor = None
        return self

    def output_prec(self, prec):
        """Set the output precision for the Magnitude.

        If not set, the the module's default will be used, set and
        queried with output_precision(prec).

        >>> a = mg(5, 'm3') ** (1/3.)  # Careful with precedence of **
        >>> print a
        1.7100 m
        >>> print a.output_prec(1)
        1.7 m
        """
        self.oprec = prec
        return self

    def output_format(self, oformat):
        """Set the output format for the Magnitude.

        If not set, the module's default will be used, set and queried
        with default_format(fmt).  Default value is "%.*f".  The star
        will be replaced by the expected output precision.

        >>> a = mg(5, 'm2').sqrt()
        >>> print a
        2.2361 m
        >>> print a.output_format("%03d")
        002 m
        """
        self.oformat = oformat
        return self

    def __coerce__(self, m):
        """Force tuples or numbers into Magnitude."""

        if not isinstance(m, Magnitude):
            if type(m) == tuple:
                if len(m) == 2:
                    r = Magnitude(m[0])
                    r._mult_by(self.sunit2mag(m[1]))
                    return self, r
                elif len(m) == 1:
                    return self, Magnitude(m[0])
                else:
                    return None
            elif _numberp(m):
                return self, Magnitude(m)
            else:
                return None
        else:
            return self, m

    def __add__(self, m):
        """Add Magnitude instances.

        >>> print mg(10, 'm') + (20, 'km') + (30, 'lightyear')
        283.8219 Pm
        """
        if m.unit != self.unit:
            raise MagnitudeError("Incompatible units: %s and %s" %
                                 (m.unit, self.unit))
        r = self.copy()
        r.val += m.val
        r.significantDigits = max( r.significantDigits, m.significantDigits )
        return r

    def __radd__(self, m):
        """Add Magnitude instances.  See __add__. """
        return self.__add__(m)

    def __iadd__(self, m):
        """Add Magnitude instances.  See __add__. """
        if m.unit != self.unit:
            raise MagnitudeError("Incompatible units: %s and %s" %
                                 (m.unit, self.unit))
        self.val += m.val
        self.significantDigits = max( self.significantDigits, m.significantDigits )
        return self

    def __sub__(self, m):
        """Substract Magnitude instances.

        >>> print mg(20, 'm/s') - (1, 'km/h')
        19.7222 m / s
        """
        if m.unit != self.unit:
            raise MagnitudeError("Incompatible units: %s and %s" %
                                 (m.unit, self.unit))
        r = self.copy()
        r.val -= m.val
        r.significantDigits = max( r.significantDigits, m.significantDigits )
        return r

    def __rsub__(self, m):
        """Substract Magnitude instances.  See __sub__."""
        return m.__sub__(self)

    def __isub__(self, m):
        """Substract Magnitude instances.  See __sub__."""
        if m.unit != self.unit:
            raise MagnitudeError("Incompatible units: %s and %s" %
                                 (m.unit, self.unit))
        self.val -= m.val
        self.significantDigits = max( self.significantDigits, m.significantDigits )
        return self

    def __mul__(self, m):
        """Multiply Magnitude instances.

        >>> print mg(10, 'm/s') * (10, 's')
        100.0000 m
        """
        r = self.copy()
        r._mult_by(m)
        return r

    def __rmul__(self, m):
        """Multiply Magnitude instances.  See __mul__."""
        r = self.copy()
        r._mult_by(m)
        return r

    def __imul__(self, m):
        """Multiply Magnitude instances.  See __mul__."""
        self._mult_by(m)
        return self

    def __div__(self, m):
        """Divide Magnitude instances.

        >>> print mg(100, 'V') / (10, 'kohm')
        10.0000 mA
        """
        r = self.copy()
        r._div_by(m)
        return r

    def __truediv__(self, m):
        """Divide Magnitude instances when "from __future__ import division"
        is in effect.

        >>> print mg(100, 'V') / (1, 'kohm')
        100.0000 mA
        """
        r = self.copy()
        r._div_by(m)
        return r

    def __rdiv__(self, m):
        """Divide Magnitude instances.  See __div__."""
        r = self.copy()
        m._div_by(r)
        return m

    def __rtruediv__(self, m):
        """Divide Magnitude instances.  See __div__."""
        r = self.copy()
        m._div_by(r)
        return m

    def __idiv__(self, m):
        """Divide Magnitude instances.  See __div__."""
        self._div_by(m)
        return self

    def __itruediv__(self, m):
        """Divide Magnitude instances.  See __div__."""
        self._div_by(m)
        return self

    def __mod__(self, n):
        """Modulus of a Magnitude by a number or a Magnitude.

        Unit is that of the left hand side operator.

        >>> print mg(10, 'm/s') % 3
        1.0000 m / s
        >>> print mg(10, 'm/s') % (3, 'W')
        1.0000 m / s
        """
        r = self.copy()
        r.val = r.val % ensmg(n).toval()
        return r

    def __imod__(self, n):
        """Modulus of a Magnitude by a number or a Magnitude.  See __mod__."""
        self.val %= n.val
        for i in range(len(self.unit)):
            self.unit[i] = self.unit[i] - n.unit[i]
        self.out_unit = None
        return self

    def __floordiv__(self, m):
        """Floordiv of two Magnitude instances.

        >>> print mg(10, 'm/s') // (3, 's')
        3.0000 m / s2
        >>> print mg(-10, 'm/s') // (3, 'm')
        -4.0000 Hz
        """
        r = self.copy()
        r._div_by(m)
        r.val = math.floor(r.val)
        return r

    def __ifloordiv__(self, m):
        """Floordiv of two Magnitude instances. See __floordiv__."""
        self._div_by(m)
        self.val = math.floor(self.val)
        return self

    def __divmod__(self, m):
        """Floordiv and remainder of two Magnitude instances.

        >>> [ str(i) for i in divmod(mg(10, 'm/s'), (3, 's')) ]
        ['3.0000 m / s2', '1.0000 m / s']
        """
        return (self.__floordiv__(m), self.__mod__(m))

    def __rdivmod__(self, m):
        """Floordiv and remainder of two Magnitude instances. See __divmod___"""
        return (m.__floordiv__(self), m.__mod__(self))

    def __pow__(self, n, modulo=None):
        """Return a Magnitude to the power n.

        If modulo is present return the result modulo it.

        >>> print mg(10, 'm/s') ** 2
        100.0000 m2 / s2
        >>> print pow(mg(10, 'km/h'), mg(2)) # Exponent cannot have dimension
        7.7160 m2 / s2
        >>> print pow(mg(10, 'm/s'), 2, 3)
        1.0000 m2 / s2
        """
        r = self.copy()
        if modulo and (r.val == math.floor(r.val)):  # it's an integer
            # might have been converted to float during creation,
            # modulo only works when all are int
            r.val = int(r.val)
        if isinstance(n, Magnitude):  # happens when called as a ** n
            if not n.dimensionless():
                raise MagnitudeError("Cannot use a dimensional number as"
                                     "exponent, %s" % (n))
            n = n.val
        r.val = pow(r.val, n, modulo)
        for i in range(len(r.unit)):
            r.unit[i] *= n
        return r

    def __ipow__(self, n):
        """Power of a Magnitude.  See __pow___."""
        if not n.dimensionless():
            raise MagnitudeError("Cannot use a dimensional number as"
                                 "exponent, %s" % (n))
        n = n.val
        self.val = pow(self.val, n)
        for i in range(len(self.unit)):
            self.unit[i] *= n
        return self

    def __neg__(self):
        """Multiply by -1 the value of the Magnitude."""
        r = self.copy()
        r.val = -r.val
        return r

    def __pos__(self):
        """Unary plus operator. """
        return self.copy()

    def __abs__(self):
        """Absolute value of a Magnitude.

        >>> print abs(mg(-10, 'm'))
        10.0000 m
        """
        r = self.copy()
        r.val = abs(r.val)
        return r

    def __cmp__(self, m):
        """Compare two Magnitude instances with the same dimensions.

        >>> print mg(10, 'm/s') > (11, 'km/h')
        True
        >>> print mg(1, 'km') == (1000, 'm')
        True
        """
        if m.unit != self.unit:
            raise MagnitudeError("Incompatible units in comparison: %s and %s" %
                                 (m.unit, self.unit))
        return cmp(self.val, m.val)

    def isIdenticalTo(self, other):
        """compare the magnitudes with all the metadata"""
        return ((self.val, self.unit, self.out_unit, self.out_factor, self.oprec, self.oformat, self.significantDigits)
                ==(other.val, other.unit, other.out_unit, other.out_factor, other.oprec, other.oformat, other.significantDigits))


    def __int__(self):
        """Return the value of a Magnitude coerced to integer.

        Note that this will happen to the value in the default output unit:

        >>> print int(mg(10.5, 'm/s'))
        10
        >>> print int(mg(10.5, 'm/s').ounit('km/h'))
        37
        """
        return int(self.toval())

    def __long__(self):
        """Return the value of a Magnitude coerced to long.  See __int__."""
        return long(self.toval())

    def __float__(self):
        """Return the value of a Magnitude coerced to float.  See __int__."""
        return float(self.toval())

    def ceiling(self):
        """Ceiling of a Magnitude's value in canonical units.

        >>> print mg(10.2, 'm/s').ceiling()
        11.0000 m / s
        >>> print mg(3.6, 'm/s').ounit('km/h').ceiling()
        4.0000 m / s
        >>> print mg(50.3, 'km/h').ceiling()
        14.0000 m / s
        """
        r = self.copy(with_format=False)
        r.val = math.ceil(r.val)
        return r

    def floor(self):
        """Floor of a Magnitude's value in canonical units.

        >>> print mg(10.2, 'm/s').floor()
        10.0000 m / s
        >>> print mg(3.6, 'm/s').ounit('km/h').floor()
        3.0000 m / s
        >>> print mg(50.3, 'km/h').floor()
        13.0000 m / s
        """
        r = self.copy()
        r.val = math.floor(r.val)
        return r

    def round(self, unit=None):
        """Round a Magnitude's value in canonical units.

        >>> print mg(10.2, 'm/s').round()
        10.0000 m / s
        >>> print mg(3.6, 'm/s').ounit('km/h').round()
        4.0000 m / s
        >>> print mg(50.3, 'km/h').round()
        14.0000 m / s
        
        >>> print mg(50.3456789, 'kHz').round('kHz')
        50.0000 kHz
        >>> print mg(50.3456789, 'kHz').round('Hz')
        50.3460 kHz
        >>> print mg(50.3, 'km / h').round('km/h')
        50.0000 km / h
        """        
        if unit:
            r = self.copy(True)
            u = self.sunit2mag(unit)
            r.val = round(r.val/u.val) * u.val
        else:
            r = self.copy()
            r.val = round(r.val)
        return r

    def to_bits(self):
        return Magnitude(math.ceil(math.log(self.val) / math.log(2.0)),
                         b=1)

    def sqrt(self):
        """Square root of a magnitude.

        >>> print mg(4, 'm2/s2').sqrt()
        2.0000 m / s
        >>> print mg(2, 'm/s').sqrt()
        1.4142 m0.5 / s0.5
        """
        return self ** 0.5


# Some helper functions

def mg(v, unit='', ounit=''):
    """Builds a Magnitude from a number and a units string.  Specify
    the preferred output unit with ounit (by default equals to unit).
    If ounit and unit have different dimensionalities unit will be
    used.

    >>> print mg(10, 'm/s')
    10.0000 m/s
    >>> a = mg(10, 'm/s', 'km/h')
    >>> print a
    36.0000 km/h
    >>> a = mg(10, 'm/s', 'kg/m')
    >>> print a
    10.0000 m/s
    >>> a = mg(1, 'B')
    >>> print a
    1.0000 B
    >>> print a.ounit('b')
    8.0000 b
    >>> a = mg(1024, 'B')
    >>> print a.ounit('b')
    8192.0000 b
    >>> print a.ounit('KiB')
    1.0000 KiB
    """
    m = Magnitude(v)
    if unit:
        u = m.sunit2mag(unit)
        m._mult_by(u)
    if not ounit or not mg(1, unit).has_dimension(ounit):
        ounit = unit
    return m.ounit(ounit)

def ensmg(m, unit=''):
    """Converts something to a Magnitude.

    >>> print ensmg(10, 'Hz')
    10.0000 Hz
    >>> print ensmg(ensmg(1000, 'Hz'))
    1000.0000 Hz
    >>> a = (4, 'mol')
    >>> print ensmg(a)
    4.0000 mol
    >>> a = mg(1024, 'Pa')
    >>> print ensmg(a)
    1024.0000 Pa
    >>> f = ensmg((10, 'Pa')) * (10, 'm2')
    >>> print f.ounit('N')
    100.0000 N
    """
    if m is None:
        return None
    if not isinstance(m, Magnitude):
        if type(m) == tuple:
            if len(m) == 2:
                return mg(m[0], m[1], unit)
            elif (len(m) == 1) and _numberp(m[0]):
                if unit:
                    return mg(m[0], unit)
                return Magnitude(m[0])
            else:
                raise MagnitudeError("Can't convert %s to Magnitude" % (m,))
        elif _numberp(m):
            if unit:
                return mg(m, unit)
            return Magnitude(m)
        else:
            raise MagnitudeError("Can't convert %s to Magnitude" % (m,))
    else:
        return m

# These don't really help much, as it's much easier to use the
# overriden * and / operators.

def __mul(m1, *rest):
    m = ensmg(m1)
    for m2 in rest:  m._mult_by(ensmg(m2))
    return m

def __div(m1, *rest):
    if rest:
        m = ensmg(m1)
        for m2 in rest:  m._div_by(ensmg(m2))
        return m
    else:
        m = Magnitude(1.0)
        m._div_by(ensmg(m1))
        return m

def new_mag(indicator, mag, isDimensionIndicator=False ):
    """Define a new magnitude understood by the package.

    Defines a new magnitude type by giving it a name (indicator) and
    its equivalence in the form of an already understood magnitude.

    >>> new_mag('mile', mg(160934.4, 'cm'))
    >>> print mg(100, 'mile/h').ounit('km/h')
    160.9344 km/h
    """
    _mags[indicator] = mag
    if isDimensionIndicator:
        _outputDimensions[tuple(mag.unit)] = indicator

def is_magnitude(m):
    return isinstance(m,Magnitude)

# Finally, define the Magnitudes and initialize _mags.


def _init_mags():
    # Magnitudes for the base SI units
    new_mag('m', Magnitude(1.0, m=1), True)
    new_mag('s', Magnitude(1.0, s=1), True)
    new_mag('K', Magnitude(1.0, K=1), True)
    new_mag('kg', Magnitude(1.0, kg=1))
    new_mag('A', Magnitude(1.0, A=1), True)
    new_mag('mol', Magnitude(1.0, mol=1), True)
    new_mag('cd', Magnitude(1.0, cd=1), True)
    new_mag('$', Magnitude(1.0, dollar=1), True)
    new_mag('dollar', Magnitude(1.0, dollar=1))
    new_mag('b', Magnitude(1.0, b=1))           # bit

    # Magnitudes for derived SI units
    new_mag('B', Magnitude(8.0, b=1))
    new_mag('rad', Magnitude(1.0))  # radian
    new_mag('sr', Magnitude(1.0))  # steradian
    new_mag('Hz', Magnitude(1.0, s=-1), True)  # hertz
    new_mag('g', Magnitude(1e-3, kg=1), True)  # gram
    new_mag('N', Magnitude(1.0, m=1, kg=1, s=-2), True)  # newton
    new_mag('Pa', Magnitude(1.0, m=-1, kg=1, s=-2), True)  # pascal
    new_mag('J', Magnitude(1.0, m=2, kg=1, s=-2), True)  # joule
    new_mag('W', Magnitude(1.0, m=2, kg=1, s=-3), True)  # watt
    new_mag('C', Magnitude(1.0, s=1, A=1), True)  # coulomb
    new_mag('V', Magnitude(1.0, m=2, kg=1, s=-3, A=-1), True)  # volt
    new_mag('F', Magnitude(1.0, m=-2, kg=-1, s=4, A=2), True)  # farad, C/V
    new_mag('ohm', Magnitude(1.0, m=2, kg=1, s=-3, A=-2), True)  # ohm, V/A
    new_mag('S', Magnitude(1.0, m=-2, kg=-1, s=3, A=2), True)  # siemens, A/V, el cond
    new_mag('Wb', Magnitude(1.0, m=2, kg=1, s=-2, A=-1), True)  # weber, V.s, mag flux
    new_mag('T', Magnitude(1.0, kg=1, s=-2, A=-1), True)  # tesla, Wb/m2, mg flux dens
    new_mag('H', Magnitude(1.0, m=2, kg=1, s=-2, A=-2), True)  # henry, Wb/A, induct.
    new_mag('degC', Magnitude(1.0, K=1))  # celsius, !!
    new_mag('lm', Magnitude(1.0, cd=1))  # lumen, cd.sr (=cd)), luminous flux
    new_mag('lux', Magnitude(1.0, m=-2, cd=1))  # lux, lm/m2, illuminance
    new_mag('Bq', Magnitude(1.0, s=-1))  # becquerel, activity of a radionulide
    new_mag('Gy', Magnitude(1.0, m=2, s=-2))  # gray, J/kg, absorbed dose
    new_mag('Sv', Magnitude(1.0, m=2, s=-2))  # sievert, J/kg, dose equivalent
    new_mag('kat', Magnitude(1.0, s=-1, mol=1))  # katal, catalitic activity

    ### Other
    # length
    new_mag("'", Magnitude(0.3048, m=1))  # feet
    new_mag('ft', Magnitude(0.3048, m=1))  # feet
    new_mag('inch', Magnitude(0.0254, m=1))  # inch
    new_mag('"', Magnitude(0.0254, m=1))  # inch
    new_mag('lightyear', Magnitude(2.99792458e8 * 365.25 * 86400, m=1))

    # volume
    new_mag('l', Magnitude(0.001, m=3))

    # time
    # year is tropical year, "the mean interval between vernal
    # equinoxes.  Differs from the sidereal year by 1 part in 26000
    # due to precession of the earth about its rotational axis
    # combined with precession of the perihelion of the earth's orbit"
    # (from units.dat).
    new_mag('year', Magnitude(31556925.974678401, s=1))
    new_mag('day', Magnitude(86400, s=1))
    new_mag('h', Magnitude(3600, s=1))
    new_mag('min', Magnitude(60, s=1))

    # Resolution
    new_mag('dpi', Magnitude(1.0 / 0.0254, m=-1))
    new_mag('lpi', Magnitude(1.0 / 0.0254, m=-1))

    # Velocity
    new_mag('ips', Magnitude(0.0254, m=1, s=-1))
    new_mag('c', Magnitude(2.99792458e8, m=1, s=-1))

    # Acceleration
    new_mag('gravity', Magnitude(9.80665, m=1, s=-2))


if not _mags:
    _init_mags()

if __name__ == '__main__':
    import doctest
    doctest.testmod()
