import pylab as pl
from scipy.optimize import leastsq


class LeastSQ_fit(object):
    """
    Perform a non-linear least squares fit to data for a function defined by
    the 'fitfunc' method.

    Public methods: 
        fitfunc:
            Place holder for inheritance. Classes that inherit this class
            should use this to return the value of the function for a given
            guess, p

        getfit:
            Return fit parameters

        plotfit:
            Use matplotlib to plot the resulting fit

    Public variables:
        p0:     array that holds guess for fit parameters
        x:      x value for raw data being fit to
        y:      y value for raw data being fit to
        sigma:  standard deviation for data being fit to.
        p:      parameters that result from least sqrs fit
        perr:   error estimate for the values in self.p
        rchisq: the reduced chisquared for the fit

    Private methods: 
        _errfunc:
            returns the distance from the target function, fitfunc

        _fit:
            perform fit and return the results

        _plotsettings:
            set up the plot properties (axes labels, title, etc.)
    """


    def __init__(self,p0,x,y,sigma,debug=False):
        """Initialization code"""

        # Initialize variables
        self.p0 = pl.array(p0)
        self.x = pl.array(x)
        self.y = pl.array(y)
        self.sigma = pl.array(sigma)
        self.debug = debug

        # perform least squares fit
        self._remove_no_errorbar()
        self.p, self.perr, self.rchisq = self._fit()
    
    """ Public methods """
    def fitfunc(self,p,x):
        """
        Place holder for classes that inherit this class. Classes that inherit this class
        should use this to return the value of the function for a given
        guess, p.
        """

        y = 0
        return y

    def getfit(self):
        """ 
        Return fit parameters
        """


        # build fit waveform for plotting        
        fitx = pl.linspace( self.x.min(), self.x.max(), 500)
        fity = self.fitfunc(self.p, fitx)
        fity_guess = self.fitfunc(self.p0, fitx)

        return self.p, self.perr, self.rchisq, fitx, fity, fity_guess

    def plotfit(self,plot_guess=False):
        """
        Use pylab to plot the resulting fit. If you would like to see your
        guess, pass the function, 'plot_guess = True', otherwise no arguments are necessary.
        """

        t = pl.linspace( self.x.min(), self.x.max(), 500)
        #pl.errorbar( self.x, self.y, yerr=self.sigma, fmt="x")
        pl.errorbar( self.x, self.y, yerr=self.sigma, fmt="ro" )
        if plot_guess:
            pl.plot( t, self.fitfunc(self.p0,t), "g-")
        pl.plot( t, self.fitfunc(self.p, t), "r-")
        self._plotsettings(plot_guess)
        pl.show()


    """ Private methods """
    
    def _debug(self):
        print
        print "----------"
        print "x:"
        print self.x
        print "y:" 
        print self.y
        print "sigma:"
        print self.sigma
        print "p"
        print self.p
        print "perr:"
        print self.perr
        print "rchisq:"
        print self.rchisq
        print "----------"
        print
    
    def _errfunc( self, p, x, y, sigma):
        """ returns the distance from the target function weighted by 1/sigma """

        return ( ( self.fitfunc(p,x) - y ) / sigma )

    def _fit(self):
        """Calculate and return the fit parameters, p; their estimated errors,
        perr; and the reduece chisqaured function, rchisq. """

        
        
            
            # Perform least squares fit
        p,cov,info,mesg,success = leastsq( self._errfunc, self.p0[:],
                args=(self.x,self.y,self.sigma), full_output=1 )
        self.p = p
    
        # Calculate the reduced chisquared
        chisq = pl.sum( info["fvec"]*info["fvec"])
        dof = pl.size(self.x) - pl.size(p)
        self.rchisq = chisq / dof
        
        # estimate error in fittied parameters (2*sigma)
        self.perr = pl.zeros(p.size)
        for j in range(p.size):
            self.perr[j] = 2*pl.sqrt( cov[j][j] * pl.sqrt(self.rchisq) )
            #self.perr[j] = 0.1
            
        # print variable info if debuggins is requested
        if self.debug: self._debug()
            
            
        return self.p, self.perr, self.rchisq

    def _plotsettings(self,plot_guess):
        pl.title("insert title")
        pl.xlabel("x")
        pl.ylabel("y")
        if plot_guess:
            pl.legend(('data', 'guess', 'fit'))
        else:
            pl.legend(('data', 'fit'))
            
    def _remove_no_errorbar(self):
        """ Remove points from data set that have sigma = 0 """
        valid_points = self.sigma != 0
        self.x = self.x[valid_points]
        self.y = self.y[valid_points]
        self.sigma = self.sigma[valid_points]
        
         

class Rabi_sinefit(LeastSQ_fit):
    """
    Fit a sine function to get the pi-pulse time.
    """
    def __init__(self,p0,x,y,sigma=1):
        """ Initialize object """
        super(Rabi_sinefit,self).__init__(p0,x,y,sigma)

    def _plotsettings(self,plot_guess):
        """ Properly label plot and display important fit parameters"""
        pl.title("insert title")
        pl.xlabel("x")
        pl.ylabel("y")
        if plot_guess:
            pl.legend(('data', 'guess', 'fit'))
        else:
            pl.legend(('data', 'fit'))

        ax = pl.axes()
        pl.text(0.6, 0.07,
             'pi-time :  %.3f +/- %.3f\n rchisq :  %.3f' % (self.p[1],
                 self.perr[1], self.rchisq),
             fontsize=16,
             horizontalalignment='left',
             verticalalignment='center',
             transform=ax.transAxes)

    def fitfunc(self, p, x):
        """ Return the value of the sine function for given fit parameters, p

        p[0]:       2*amplitude
        p[1]:       pi-pulse time
        p[2]:       the offset from zero for the center of the sine function
        """
        return p[0] / 2 * pl.sin( pl.pi/p[1]*x + pl.pi*3/2 ) + p[2]

class F_uWave_exp_fit(LeastSQ_fit):
    """
    Fit a sine function to get the pi-pulse time.
    """
    def __init__(self,p0,x,y,sigma,debug=False):
        """ Initialize object """
        super(F_uWave_exp_fit,self).__init__(p0,x,y,sigma,debug)

    def _plotsettings(self,plot_guess):
        """ Properly label plot and display important fit parameters"""
        pl.title("UWave freq. scan")
        pl.xlabel("freq. (MHz)")
        pl.ylabel("f=4 probability")
        if plot_guess:
            pl.legend(('data', 'guess', 'fit'))
        else:
            pl.legend(('data', 'fit'))

        ax = pl.axes()
        pl.text(0.6, 0.07,
                ('center :  %.3f +/- %.3f\n' + 'waist: %.3f+/- %.3f\n' +
                    'rchisquared: %.3f') %(self.p[1], self.perr[1], self.p[2],
                        self.perr[2], self.rchisq),
             fontsize=16,
             horizontalalignment='left',
             verticalalignment='center',
             transform=ax.transAxes)

    def fitfunc(self, p, x):
        """ Return the value of the sine function for given fit parameters, p

        p[0]:       amplitude
        p[1]:       gaussian center
        p[2]:       guassian waist
        p[3]:       offset from 0
        """
        return -p[0] * pl.exp( -2*(x-p[1])**2 / (p[2]**2) ) + p[3]

# Uncomment to test code
def main():
#    data = pl.zeros((3,3))
#    data = pl.loadtxt("rabiFlopData.txt")
#    y = data[:,1]
#    sig = data[:,2]
    x = pl.array([7.2, 7.3, 7.35, 7.4, 7.5, 7.6])
    y = pl.array([0.8, 0.6, 0.05, 0.1, 0.5, 0.8])
    sig = pl.array([0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
     

    
    p0 = [0.8,7.37,0.1,0.9]
    thefit = F_uWave_exp_fit(p0,x,y,sig, debug = True)
    p, perr, rchisq, fitx, fity, fity_guess = thefit.getfit()
    pl.errorbar(x,y,sig,fmt='ro')
    pl.plot(fitx,fity,'r-')
    
    x = pl.array([7.2, 7.3, 7.35, 7.4, 7.45, 7.5, 7.6, 7.7])
    y = pl.array([0.7, 0.62, 0.05, 0.1, 0.12, 0.5, 0.8, 0.9])
    sig = pl.array([0.1, 0.1, 0.1, 0.05, 0.1, 0.1, 0.1, 0.1])
    thefit = F_uWave_exp_fit(p0,x,y,sig, debug = True)
    p, perr, rchisq, fitx, fity, fity_guess = thefit.getfit()
  
   
    pl.errorbar(x,y,sig,fmt='go')
    pl.plot(fitx,fity,'g-')
    pl.show()
    

if __name__ == '__main__':
    main()
