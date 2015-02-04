// $Id: Pchip.h 232 2014-10-02 16:32:27Z  $
// $HeadURL: http://192.168.254.234:1080/svn/CI/4000/4062_4122/Branches/PassViSession/Estimation/Pchip.h $
//
// (C) 2014 MagiQ Technologies, Inc.

#ifndef PCHIP_H
#define PCHIP_H
#include <vector>
#include <cmath>

namespace pchip {

	using namespace std;

	class Pchip {
	public:

		Pchip(vector<double>& x, vector<double>& y); // Creates a piecewise Cubic spline over the range of X values.
		double GetValue(double x) const; // return the estimated value using the pchip line generated.  

	private:
        vector< vector<double> > coefs;
		vector<double> breaks;

		static vector<double> Diff(vector<double>& diff);
        // Moved function body here to get it inlined
        static inline int Sign(double value) {
            if(value > 0)
                return 1;
            else if (value < 0)
                return -1;
            else
                return 0;
        }
	};
}

#endif //PCHIP_H
