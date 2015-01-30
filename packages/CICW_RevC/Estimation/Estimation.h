// $Id: Estimation.h 278 2014-11-07 15:42:33Z greg $
// $HeadURL: http://192.168.254.234:1080/svn/CI/4000/4062_4122/Trunk/Estimation/Estimation.h $

#ifndef _ESTIMATION_H
#define _ESTIMATION_H
#include <vector>
#include <map>
#include <string>
#include <math.h>       // M_PI
#include "Pchip.h"

namespace Estimation
{
	using namespace std;
    using namespace pchip;

    struct PchipFunctions {
		vector<Pchip> gain0;
		vector<Pchip> gain0attn;
		vector<Pchip> gain9;
		vector<Pchip> attn;
		vector<Pchip> pmin;
	}; 

    class MeasuredValues {
      public:
		vector<double>              freq;
		vector<double>              temp;
		vector<double>              attnFreq;
		vector<double>              pow0;       // not used in lookup
        vector<double>              pow9;       // not used in lookup
		vector<double>              pow0attn;   // not used in lookup
		vector<double>              pow9min;    // not used in lookup
		vector<double>              pdac;       // not used in lookup
        vector< vector<double> >    attnPow;    // not used in lookup
		vector<double>              attnTemp;   // not used in lookup
		bool                        card4122;   // applies to all data - does not belong here
		PchipFunctions              calFunc;
	};

    enum GainSetting {
        gain9 = 0,
        gain0 = 1,
        gain0attn = 2
    };

    class CalculateEstimates
	{
        class fspHolder {
          public:
            fspHolder();
        };
    public:
		CalculateEstimates(const MeasuredValues* value);
		CalculateEstimates(const vector<short>& buffer);

		void AddNewValues(const vector<short>& buffer);
		void AddNewValues(const MeasuredValues* value);
		
		vector<unsigned short> GetPdacValue(double freq, double pow, double temp, double vco, double cap); // estimates based on temperature and vco/cap
		vector<unsigned short> GetPdacValue(double freq, double pow, double temp); // estimates based on temperature
		bool isCard4122() { return (values.size() > 0)? values[0].card4122 : false; }
		int calDataCount() { return (int)values.size(); }

	private:
		vector<MeasuredValues> values;
        map<double, double>    vcoFsp;
        map<double, bool>      capFsp;

		// Estimates that account for temperature
		double GetPmaxEstimate(double freq, GainSetting setting, double temp, double vco, double cap);
		double GetPmaxEstimate(double freq, GainSetting setting, double temp);
		double GetPminEstimate(double freq, double temp, double vco, double cap);
		double GetPminEstimate(double freq, double temp);
		void SetupCalFunc(MeasuredValues* value);
        void setupFsp(void);
		void initializeFsp();
        static const vector<const double>       fsp4122;
        static const vector<const double>       pminfsp4122;
        static const vector<const double>       fsp;
        static const vector<const double>       pminfsp;
        static const fspHolder                  fH;
	};	
}		
#endif
