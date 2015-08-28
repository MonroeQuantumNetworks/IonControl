// $Id: Pchip.cpp 266 2014-10-30 21:25:39Z matt $
// $HeadURL: http://192.168.254.234:1080/svn/CI/4000/4062_4122/Trunk/Estimation/Pchip.cpp $
//
// (C) 2014 MagiQ Technologies, Inc.

#include "stdafx.h"
#include <algorithm>    // std::sort
#include "Pchip.h"

using namespace pchip;

Pchip::Pchip(vector<double>& x, vector<double>& y) :
    coefs(x.size()-1,vector<double>(4)),
    breaks(x)
{
	unsigned n = (int)x.size()-1;

	if(n+1 < 3 || n != y.size()-1) {
//        assert(0);  /// @TODO Really want a throw here since ctor is failing.
		return; // There needs to be at least three points for this to work correctly.
    }

	vector<double> dx(Diff(x));
	vector<double> dydx(Diff(y));
	vector<double> slopes(n+1);

	for (unsigned i = 0; i < dydx.size(); i++)
		dydx[i] = dydx[i]/dx[i];

	// Determine the first value
	slopes[0] = ((2*dx[0]+dx[1])*dydx[0] - dx[0]*dydx[1]) / (dx[1]+dx[0]);
	if(Sign(slopes[0]) != Sign(dydx[0]))
		slopes[0] = 0;
	else if(Sign(dydx[0]) != Sign(dydx[1]) && abs(slopes[0]) > abs(3*dydx[0]))
		slopes[0] = 3*dydx[0];

	// Determine all values between the first and last value
	double dmin, dmax, w1, w2;
	for(unsigned i = 0; i < dydx.size()-1; i++){
		if(dydx[i] == 0 && dydx[i+1] == 0)
			slopes[i+1] = 0;
		else if(Sign(dydx[i]) == Sign(dydx[i+1])){
			dmax = max(dydx[i], dydx[i+1]);
			dmin = min(dydx[i], dydx[i+1]);
			w1 = (dx[i]*2 + dx[i+1]) / (3*(dx[i] + dx[i+1]));
			w2 = (dx[i] + dx[i+1]*2) / (3*(dx[i] + dx[i+1]));
			slopes[i+1] = dmin / ((w1*dydx[i]/dmax) + (w2*dydx[i+1]/dmax));
		} else
			slopes[i+1] = 0;
	}

	// And then finish off slopes and get the last value. 
	slopes[n] = ((2*dx[n-1]+dx[n-2])*dydx[n-1] - dx[n-1]*dydx[n-2]) / (dx[n-2]+dx[n-1]);
	if(Sign(slopes[n]) != Sign(dydx[n-1]))
		slopes[0] = 0;
	else if(Sign(dydx[n-1]) != Sign(dydx[n-2]) && abs(slopes[n]) > abs(3*dydx[n-1]))
		slopes[n] = 3*dydx[n-1];

	for(unsigned i = 0; i < dydx.size(); i++) {
		w1 = (dydx[i]-slopes[i]) / dx[i];
		w2 = (slopes[i+1]-dydx[i]) / dx[i];
		coefs[i][0] = (w2 - w1) / dx[i];
		coefs[i][1] = 2*w1 - w2;
		coefs[i][2] = slopes[i];
		coefs[i][3] = y[i];
	}
}


vector<double> Pchip::Diff (vector<double>& diff) {
	vector<double> retDiff(diff.size()-1); 
	for (unsigned i = 0; i < diff.size()-1; i++)
		retDiff[i] = diff.at(i+1) - diff.at(i);
	return retDiff;
}


double Pchip::GetValue(double x) const {
	double dx;
    unsigned iii;
    // Using binary search instead of linear search is a HUGE runtime improvement
    vector<double>::const_iterator bgn = breaks.begin();
    // upper_bound finds value greater than requested.
    vector<double>::const_iterator igt = std::upper_bound(bgn+1,
                                                          (vector<double>::const_iterator)breaks.end()-1,
                                                          x);
    iii = (unsigned)(igt-bgn);
    --iii;

    // Moving formula outside loop and getting rid of pow() moved this from #2 spot in profile
    // to #3, but overall percentage didn't change much; fraction of a second oveall improvement
	dx = x - breaks[iii];
    double dx2 = dx*dx;
    double dx3 = dx2*dx;
	return dx3*coefs[iii][0] + dx2*coefs[iii][1] + dx*coefs[iii][2] + coefs[iii][3];
}
