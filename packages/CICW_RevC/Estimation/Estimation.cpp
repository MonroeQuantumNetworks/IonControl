// $Id: Estimation.cpp 266 2014-10-30 21:25:39Z matt $
// $HeadURL: http://192.168.254.234:1080/svn/CI/4000/4062_4122/Trunk/Estimation/Estimation.cpp $
//
// (C) 2014 MagiQ Technologies, Inc.

#include "stdafx.h"
#include <assert.h>
#define _USE_MATH_DEFINES
#include <cmath>
#include <algorithm>    // std::sort
#include "Pchip.h"
#include "Estimation.h"

// Defined in math.h
// #define M_PI (std::atan(1.0)*4.0)

using namespace pchip;
using namespace Estimation;

//#if _MSC_VER < 12
// C++ 11 supports an initializer list, but that requires Visual Studio 2013
// or another newer compiler.  (I really don't like declaring an initializer
// array just to copy it into a const vector.)
static const double fsp4122_arr[] = {6000, 7800, 8800, 12001};
const vector<const double> Estimation::CalculateEstimates::fsp4122(
    fsp4122_arr, fsp4122_arr + sizeof(fsp4122_arr) / sizeof(fsp4122_arr[0]));
//#else
//const vector<const double> Estimation::CalculateEstimates::fsp4122(
//    initializer_list<double>{6000, 7800, 8800, 12001});
//#endif

static const double pminfsp4122_arr[] = {6000, 7800, 8800, 9080,12001};
const vector<const double> Estimation::CalculateEstimates::pminfsp4122 = vector<const double>(
    pminfsp4122_arr, pminfsp4122_arr + sizeof(pminfsp4122_arr) / sizeof(pminfsp4122_arr[0]));

static const double fsp_arr[] = {0,145,195,280,460,750,1200,1499.999999,1570,1830,1985,2258,2402,\
                       2656,2808,2999.999999,3129,3661,4365,4505,4804,5100,5200,5315,5603,6001};
const vector<const double> Estimation::CalculateEstimates::fsp = vector<const double>(
    fsp_arr, fsp_arr + sizeof(fsp_arr) / sizeof(fsp_arr[0]));

static const double pminfsp_arr[] = {0,750,1499,2255,3650,4525,6001};
const vector<const double> Estimation::CalculateEstimates::pminfsp = vector<const double>(
    pminfsp_arr, pminfsp_arr + sizeof(pminfsp_arr) / sizeof(pminfsp_arr[0]));

const double freq_arr[] = {
    75, 170, 265, 370, 610, 745, 755, 900, 1210, 1400, 1503, 1751, 2001, 2236, 2351, 2951, 3351, 3501, 3601, \
    3701, 3871, 3950, 4001, 4251, 4401, 4441, 4461, 4481, 4501, 4516, 4536, 4701, 5101, 5551, 5776, 5901, 6000};
static const vector<const double> freq_vec(freq_arr, freq_arr + sizeof(freq_arr) / sizeof(freq_arr[0]));



// static const guarantees loader initializes this object when DLL loaded -->
// no thread safety issues as when tried to initialze from other functions.
//map<double,double> Estimation::CalculateEstimates::fspHolder::vcoFsp;
//map<double,bool>   Estimation::CalculateEstimates::fspHolder::capFsp;

void Estimation::CalculateEstimates::initializeFsp() {
    /*
      fsp0high = [2656, 2808,14; 5315,5603,25];
      fsp0low = [2808,3000,15; 5603,6000,26];  
      fsp1high = [2258,2402,12;4525,4804,21];
      fsp1low = [2402,2656,13;4804,5100,22;5100,5200,23;5200,5315,24];
      fsp2high = [1830,1985,10;3661,3975,18];
      fsp2low = [1985,2258,11;3975,4470,19;4470,4525,20];
      fsp3high = [1500,1570,8;3000,3129,16];
      fsp3low = [1570,1830,9;3129,3661,17]; 
    */
    // Set up all of the VCO value based on frequency
    vcoFsp.insert(pair<double,double>(1570,3)); 
    vcoFsp.insert(pair<double,double>(1830,3));
    vcoFsp.insert(pair<double,double>(1985,2)); vcoFsp.insert(pair<double,double>(2258, 2));
    vcoFsp.insert(pair<double,double>(2402,1)); vcoFsp.insert(pair<double,double>(2656,1));
    vcoFsp.insert(pair<double,double>(2808,0)); vcoFsp.insert(pair<double,double>(3000,0));
    vcoFsp.insert(pair<double,double>(3129,3)); vcoFsp.insert(pair<double,double>(3661,3));
    vcoFsp.insert(pair<double,double>(3975,2)); vcoFsp.insert(pair<double,double>(4365,2)); vcoFsp.insert(pair<double,double>(4505,2));
    vcoFsp.insert(pair<double,double>(4804,1)); vcoFsp.insert(pair<double,double>(5100,1)); vcoFsp.insert(pair<double,double>(5200,1)); vcoFsp.insert(pair<double,double>(5315,1));
    vcoFsp.insert(pair<double,double>(5603,0)); vcoFsp.insert(pair<double,double>(6001,0));

    // And set if the cap is high or low for each of the frequencies. 
    capFsp.insert(pair<double,bool>(1570,true)); capFsp.insert(pair<double,bool>(1830,false));
    capFsp.insert(pair<double,bool>(1985,true)); capFsp.insert(pair<double,bool>(2258,false));
    capFsp.insert(pair<double,bool>(2402,true)); capFsp.insert(pair<double,bool>(2656,false));
    capFsp.insert(pair<double,bool>(2808,true)); capFsp.insert(pair<double,bool>(3000,false));
    capFsp.insert(pair<double,bool>(3129,true)); capFsp.insert(pair<double,bool>(3661,false));
    capFsp.insert(pair<double,bool>(3975,true)); capFsp.insert(pair<double,bool>(4365,false)); capFsp.insert(pair<double,bool>(4505,false));
    capFsp.insert(pair<double,bool>(4804,true)); capFsp.insert(pair<double,bool>(5100,false)); capFsp.insert(pair<double,bool>(5200,false)); capFsp.insert(pair<double,bool>(5315,false));
    capFsp.insert(pair<double,bool>(5603,true)); capFsp.insert(pair<double,bool>(6001,false));
}


/// <summary>
/// Takes in a pre-created MeasuredValues structure. <para>The structure is made by the 
/// EePromViewer class primarily, or you can bypass the GUI and call CalculateEstimates with the 
/// straight buffer array read from memory</para>
/// </summary>
CalculateEstimates::CalculateEstimates(const MeasuredValues* value) {
    // This is a ctor.  By definition the object is empty --> don't need to clear anything.
	initializeFsp();
	AddNewValues(value);
}

/// <summary>
/// AddNewValues is used to add more than one MeasuredValues structure to the object, allowing for multiple temperature profiles. 
/// </summary>
void CalculateEstimates::AddNewValues(const MeasuredValues* value) {
    assert(value->temp.size() > 0);

    MeasuredValues* vvv = NULL;
	bool placed = false;
	unsigned size = (unsigned)values.size();

	for (unsigned i = 0; i < size; i++) {
		if(value->temp[0] < values[i].temp[0]) {
            // This is a COPY - would be nice to just assign values to new vector
			vvv = &*values.insert(values.begin() + i, *value);
			placed = true;
			break;
		}
	} 
    if (placed == false) {
        values.push_back(*value);
        vvv = &values.back();
    }
    assert(vvv);

    SetupCalFunc(vvv);
}

/// <summary>
/// Creates an estimation object using the direct buffer array pulled from the EeProm. 
/// </summary>
CalculateEstimates::CalculateEstimates(const vector<short>& buffer) {
	initializeFsp();
	AddNewValues(buffer);
}

/// <summary>
/// AddNewValues(vector<short>) adds EEPROM data measured values
/// </summary>
void CalculateEstimates::AddNewValues(const vector<short>& buffer) {
    //	vector<short> buffer = buf;
	bool updatedVersion = buffer[10] != (short)-1 && buffer[10];
	bool card4122 = buffer[7] == (short)4122;
	unsigned freqLen, pdacLen, pdacPowLen, headerLen, pdacStart, pdacFreqLen;
	if(updatedVersion == false) {
		freqLen = buffer[0]/2;
		pdacLen = buffer[1]/2;
		pdacPowLen = buffer[2]/2;
		headerLen = buffer[4]/2;
		pdacStart = buffer[5]/2;	
	} else {
		freqLen = buffer[0];
		pdacLen = buffer[1];
		pdacPowLen = buffer[2];
		headerLen = buffer[4];
		pdacStart = buffer[5];	
	}
	pdacFreqLen = buffer[6];

	unsigned i;
	MeasuredValues value;
	if(updatedVersion == false) {
		if(card4122 == false){
			value.attnFreq = vector<double>(freq_vec.begin(), freq_vec.end());
		} else {
			value.attnFreq = vector<double>(freqLen);
		}
	} else {
		value.attnFreq = vector<double>(pdacFreqLen);
		for(i = 0; i < pdacFreqLen; i++) {
			value.attnFreq.at(i) = buffer[i+pdacStart+pdacPowLen+pdacLen];
		}
	}
	value.pdac = vector<double>(pdacLen);
	value.attnTemp = vector<double>(pdacLen);
	value.card4122 = card4122;

	for(i = 0; i < freqLen; i++) {
		value.freq.push_back(buffer[i+headerLen]);	// Frequencies
		if(card4122) {
			value.pow9.push_back((double)buffer[i+headerLen+freqLen]/100.0); // Gain 9 for 4122 card
			value.temp.push_back(buffer[i+headerLen+2*freqLen]); // temperature for 4122 card
			value.pow9min.push_back((double)buffer[i+headerLen+3*freqLen]/100.0); // Gain 9 at pmin
		} else {
			value.pow0.push_back((double)buffer[i+headerLen+freqLen]/100.0); // Gain 0
			value.pow9.push_back((double)buffer[i+headerLen+2*freqLen]/100.0); // Gain 9 for 4062 card
			value.temp.push_back(buffer[i+headerLen+3*freqLen]); // temperature for 4062 card
			value.pow0attn.push_back((double)buffer[i+headerLen+4*freqLen]/100.0); // Gain 0 at 3120 attn
		}
	}
	if(card4122 && updatedVersion == false) {
		for(i = 0; i < value.freq.size(); i++)
			value.attnFreq[i] = value.freq[i];
	}

	// Set the size for the attnPow array after reading off the frequencies. 
    value.attnPow = vector< vector<double> >();

	int index = (pdacStart); 
	for(i = pdacStart; i < (pdacStart+pdacLen); i++)
		value.pdac[i-pdacStart] = buffer[i];// PDAC values

	index = (pdacStart+pdacLen); 
	for(i = 0; i < pdacLen; i++) {
		vector<double> attnPowFreq; // Create the row vector
		for (unsigned j = 0; j < pdacFreqLen; j++) 
			attnPowFreq.push_back((double)buffer[(i*pdacFreqLen)+j+index]/100.0);
			//value.attnPow.SetValue((double)buffer[(i*pdacFreqLen)+j+index]/100.0, i, j); // PDAC power readings	
		value.attnPow.push_back(attnPowFreq);
	}
    
    // Build splines - BEFORE copying object into values vector.
    SetupCalFunc(&value);

	bool placed = false;
    if (values.size() > 0) {
        vector<MeasuredValues>::iterator vvv = values.begin();
        for (; vvv != values.end(); ) {
            if (value.temp[0] < vvv->temp.at(0)) {
                values.insert(vvv,value);
                placed = true;
                break;
            }
            vvv++;
        }
    }
	if(placed == false)
		values.push_back(value);
}

/// <summary>
/// Private function that takes the saved values, and interpolates pchip lines between points. 
/// These equations are what is primarily used to estimate everything. 
/// </summary>
void CalculateEstimates::SetupCalFunc(MeasuredValues* value) {
	unsigned indexCount = 0, lowerIndex;
	unsigned index[50];
	bool indexSet = false;
	vector<double> freqSubset;
	vector<double> powSubset;
	vector<double> maxAttn(value->attnFreq.size());	
	vector<double> freqSubsetSorted;

    // Clear any old coefficients
    value->calFunc.gain0.clear();
    value->calFunc.gain0attn.clear();
    value->calFunc.gain9.clear();
    value->calFunc.attn.clear();
    value->calFunc.pmin.clear();

	if(value->card4122 == false) {

		for(unsigned i = 0; i < fsp.size()-1; i++){
			indexSet = false;
			indexCount = 0;
			// Figure out what indexes refer to the next prediction interval
			freqSubsetSorted.clear();
			map<double,int> freqIndex;
			for(unsigned j = 0; j < value->freq.size(); j++) {
				if(fsp.at(i) < value->freq.at(j) && value->freq.at(j) < fsp.at(i+1)) {
					freqIndex.insert(pair<double,int>(value->freq.at(j), j));
					freqSubsetSorted.push_back(value->freq.at(j));
					indexCount++;
				}
			}
			// This is to sort the frequencies and powers
			sort(freqSubsetSorted.begin(), freqSubsetSorted.end());
			for (unsigned j = 0; j < indexCount; j++) {
				index[j] = freqIndex[freqSubsetSorted[j]];
			}

			// Create pchip estimations for pmax
			freqSubset = vector<double>(indexCount);
			powSubset = vector<double>(indexCount);
			for (unsigned j = 0; j < indexCount; j++) {
				freqSubset[j] = value->freq[index[j]];
				powSubset[j] = value->pow0[index[j]];
			}
			value->calFunc.gain0.push_back(Pchip(freqSubset, powSubset));

			for (unsigned j = 0; j < indexCount; j++) 
				powSubset[j] = value->pow9[index[j]];
			value->calFunc.gain9.push_back(Pchip(freqSubset, powSubset));

			for (unsigned j = 0; j < indexCount; j++) 
				powSubset[j] = value->pow0attn[index[j]];
			value->calFunc.gain0attn.push_back(Pchip(freqSubset, powSubset));
		}

		bool reverseBool = false;
		if(value->pdac[0] > value->pdac[value->pdac.size()-1]) {
			reverse(value->pdac.begin(), value->pdac.end());
			reverseBool = true;
		}
		// Create estimates for the attn, and get the maximum attenuation at each freq
		for(unsigned i = 0; i < value->attnFreq.size(); i++) { 
			powSubset = vector<double>(value->pdac.size());
			for(unsigned j = 0; j < value->pdac.size(); j++) {
				powSubset[j] = value->attnPow[j][i];
			} 
			if(reverseBool) reverse(powSubset.begin(), powSubset.end());
			value->calFunc.attn.push_back(Pchip(value->pdac, powSubset));
			if(reverseBool)
				maxAttn[i] = value->attnPow[value->pdac.size()-1][i] - value->attnPow[0][i];
			else
				maxAttn[i] = value->attnPow[0][i] - value->attnPow[value->pdac.size()-1][i];
		}

		for(unsigned i = 0; i < pminfsp.size()-1; i++){
			indexSet = false;
			indexCount = 0;
			// Figure out what indexes refer to the next prediction interval
			for(unsigned j = 0; j < value->attnFreq.size(); j++) {
				if(pminfsp.at(i) < value->attnFreq[j] && value->attnFreq[j] < pminfsp.at(i+1)) {
					if(indexSet == false) {	
						indexSet = true;
						lowerIndex = j;
					}
					indexCount++;
				}
			}
			freqSubset = vector<double>(indexCount);
			powSubset = vector<double>(indexCount);
			for (unsigned j = lowerIndex; j < (indexCount+lowerIndex); j++) {
				freqSubset[j-lowerIndex] = value->attnFreq[j];
				powSubset[j-lowerIndex] = maxAttn[j];
			}
			value->calFunc.pmin.push_back(Pchip(freqSubset, powSubset));
		}
	} else { //4122 code:

		// Go through and set all of the pmax and pmin pchip estimation lines
		for(unsigned i = 0; i < fsp4122.size()-1; i++){
			indexCount = 0;
			// Figure out what indexes refer to the next prediction interval
			for(unsigned j = 0; j < value->freq.size(); j++) {
				if(fsp4122.at(i) < value->freq[j] && value->freq[j] < fsp4122.at(i+1)) {
					index[indexCount] = j;
					indexCount=indexCount+1;
				}
			}
			// Create pchip estimations for pmax
			freqSubset = vector<double>(indexCount);
			powSubset = vector<double>(indexCount);
			for (unsigned j = 0; j < indexCount; j++) {
				freqSubset[j] = value->freq[index[j]];
				powSubset[j] = value->pow9[index[j]];
			}
			value->calFunc.gain9.push_back(Pchip(freqSubset, powSubset));
		}

		// Go through and set all of the pmax and pmin pchip estimation lines
		for(unsigned i = 0; i < pminfsp4122.size()-1; i++){
			indexCount = 0;
			// Figure out what indexes refer to the next prediction interval
			for(unsigned j = 0; j < value->freq.size(); j++) {
				if(pminfsp4122.at(i) < value->freq[j] && value->freq[j] < pminfsp4122.at(i+1)) {
					index[indexCount] = j;
					indexCount=indexCount+1;
				}
			}
			// Create pchip estimations for pmax
			freqSubset = vector<double>(indexCount);
			powSubset = vector<double>(indexCount);
			for (unsigned j = 0; j < indexCount; j++) {
				freqSubset[j] = value->freq[index[j]];
				powSubset[j] =  value->pow9min[index[j]];
			}
			value->calFunc.pmin.push_back(Pchip(freqSubset, powSubset));

		}
		bool reverseBool = false;
		if(value->pdac[0] > value->pdac[value->pdac.size()-1]) {
			reverse(value->pdac.begin(), value->pdac.end());
			reverseBool = true;
		}
		// and then go through and create attn estimation lines. 
		for(unsigned i = 0; i < value->freq.size(); i++) { 
			powSubset = vector<double>(value->pdac.size());
			for(unsigned j = 0; j < value->pdac.size(); j++) {
				powSubset[j] = value->attnPow[j][i];
			}
			if(reverseBool) reverse(powSubset.begin(), powSubset.end());
			value->calFunc.attn.push_back(Pchip(value->pdac, powSubset));
		}
	}
}

#pragma region Temperature Functions

//========================================================================================
// Helper functions for the temperature dependent functions
//========================================================================================
double CalculateEstimates::GetPmaxEstimate(double freq, GainSetting setting, double temp) {
	return GetPmaxEstimate(freq, setting, temp, -1, -1);
}

double CalculateEstimates::GetPminEstimate(double freq, double temp){
	return GetPminEstimate(freq, temp, -1, -1);
}

vector<unsigned short> CalculateEstimates::GetPdacValue(double freq, double pow, double temp) {
	return GetPdacValue(freq, pow, temp, -1, -1);
}

//========================================================================================
// These functions return the estimated values and are also affected by temperature. The more temperature profiles saved to a card, 
// the more accurate the return values from these functions will be. If values.size() == 1, these will return the same thing as normal.
//========================================================================================
double CalculateEstimates::GetPmaxEstimate(double freq, GainSetting setting, double temp, double vco, double cap) { 
	double vcoEst;
	unsigned int index;
	bool capHigh;
	int valueIndex = -1;
	MeasuredValues* value = NULL;
	bool notEnoughValues = false;
	if(values.size() <= 2) { // return the normal value if there is only one temperature profile available. 
        double closestFreq = 100000, closestTemp = 100000;
		for(unsigned j = 0; j < values.size(); j++) {
			value = &values.at(j);
			for(unsigned i = 0; i < value->freq.size(); i++){
				if(closestFreq >= abs(freq-value->freq.at(i))) {
					closestFreq = abs(freq-value->freq.at(i));
					if(closestTemp > abs(temp - value->temp.at(i))){
						closestTemp = abs(temp - value->temp.at(i));
						valueIndex = j;
					}
				}
			}
		}
		if(valueIndex == -1)
			return -1;
        notEnoughValues = true;
    }

	vector<double> pmaxvalues = vector<double>(values.size());
	vector<double> tempvalues = vector<double>(values.size());

	for (unsigned j = 0; j < values.size(); j++){
		if(notEnoughValues) {
			value = &values.at(valueIndex);
        } else {
			value = &values.at(j);

#if 1
/// @TODO This code appears 3 times - extract into function.
            // freqs not sorted
            double closestFreq = 10000;
			for(unsigned i = 0; i < value->freq.size(); i++){
				if(closestFreq > abs(freq-value->freq.at(i))) {
					closestFreq = abs(freq-value->freq.at(i));
					tempvalues[j] = value->temp.at(i);
				}
			}
#else
            assert(std::is_sorted(value->freq.begin(),value->freq.end()));
            vector<double>::const_iterator igt = std::upper_bound(
                value->freq.begin()+1, value->freq.end()-1, freq);
            index = igt - value->freq.begin();
            double diff = fabs(freq - *igt);
            double diff_2 = fabs(freq - value->freq[index-1]);
            // Want temperature of closer frequency.
            if (diff < diff_2)
                tempvalues[j] = value->temp[index];
            else
                tempvalues[j] = value->temp[index-1];
#endif
        }
		if(value->card4122 == false) {
            unsigned int i;
			for (i = 1; i < fsp.size(); i++) {
				if(freq <= fsp.at(i))
                    break;
            }
            if (freq < 1500 || vco == -1 || cap == -1) {
                index = i-1;
            } else {
                vcoEst  = vcoFsp[fsp.at(i)];
                capHigh = capFsp[fsp.at(i)];
                if(vco == vcoEst) {
                    if(capHigh == (cap > 15)) // The cap and vco are correct. Use standard estimate at that point.
                        index = i-1;
                    else if (capHigh == false && cap>15 == true){ 
                        if(fsp.at(i) != 4365)// Cap switched late, use the previous estimate
                            index = i-2;
                        else // Cap is ignored in this band, so just use the current value
                            index = i-1;
                    } else 
                        index = i;
                } else if(vco < vcoEst) // Vco switched early, use the next section's estimate
                    index = i;
                else //vco > vcoEst; Vco switched late, use the estimate for the previous Vco
                    index = i-2;
            }
            if(value->calFunc.gain9.size() <= index || index < 0)
                index = i-1;
			 
			Pchip *hhh = NULL;
			unsigned maxidx;
            switch (setting)
            {
            case gain9:
				hhh = &value->calFunc.gain9.at(index);
				maxidx = (unsigned)value->calFunc.gain9.size()-1;
                pmaxvalues[j] = value->calFunc.gain9.at(index).GetValue(freq);
                break;
            case gain0:
				hhh = &value->calFunc.gain0.at(index);
				maxidx = (unsigned)value->calFunc.gain0.size() - 1;
				pmaxvalues[j] = value->calFunc.gain0.at(index).GetValue(freq);
                break;
            case gain0attn:
				hhh = &value->calFunc.gain0attn.at(index);
				maxidx = (unsigned)value->calFunc.gain0attn.size() - 1;
				pmaxvalues[j] = value->calFunc.gain0attn.at(index).GetValue(freq);
                break;
            default:
                break;
            }
			/*/
			assert(hhh->breaks[0] - 30 <= freq &&
				hhh->breaks[hhh->breaks.size() - 1] + 30 >= freq ||
				(index == 0 && freq < hhh->breaks[0]) ||
				(index == maxidx && freq > hhh->breaks[hhh->breaks.size() - 1]) ||
				-1 == (int)vco);
			//*/

		} else {
            if(setting == gain9){
                unsigned i;
				for (i = 1; i < fsp4122.size(); i++) {				
					if(freq <= fsp4122.at(i))
						break;
				} 
                index = i-1;
                pmaxvalues[j] = value->calFunc.gain9.at(index).GetValue(freq);
			} else {// The process is identical for pmin on a 4122. This is secretly referenced by GetPminEstimate
                unsigned i;
				for (i = 1; i < pminfsp4122.size(); i++) {				
					if(freq <= pminfsp4122.at(i))
						break;
				}
                index = i-1;
                pmaxvalues[j] = value->calFunc.pmin.at(index).GetValue(freq);
			}
		}
        if(notEnoughValues)
            return pmaxvalues[j];
	}
	Pchip ret(tempvalues, pmaxvalues);
	return ret.GetValue(temp);
}

double CalculateEstimates::GetPminEstimate(double freq, double temp, double vco, double cap) {

    if (values[0].card4122)
        // Used for 4122 pmin, because it's not an estimated value.
        return GetPmaxEstimate(freq, gain0, temp, vco, cap);

	double pmax;
	int valueIndex = -1;
	MeasuredValues *value = NULL;
	bool notEnoughValues = false;

	if(values.size() <= 2) { // return the normal value if there is only one temperature profile available. 
        double closestTemp = 100000;
        double closestFreq = 100000;
		for(unsigned j = 0; j < values.size(); j++) {
			value = &values.at(j);
			for(unsigned i = 0; i < value->freq.size(); i++){
				if(closestFreq >= abs(freq-value->freq.at(i))) {
					closestFreq = abs(freq-value->freq.at(i));
					if(closestTemp > abs(temp - value->temp.at(i))){
						closestTemp = abs(temp - value->temp.at(i));
						valueIndex = j;
					}
				}
			}
		}
		if(valueIndex == -1)
			return -1;
		notEnoughValues = true;
	}

	vector<double> pminvalues = vector<double>(values.size());
	vector<double> tempvalues = vector<double>(values.size());
    pmax = GetPmaxEstimate(freq,gain9,temp,vco,cap);
	for (unsigned j = 0; j < values.size(); j++){
        unsigned index;
		if(notEnoughValues) // If there aren't enough for the cubic, it uses the closest temp
			value = &values.at(valueIndex);
		else {
			value = &values.at(j);
            
            // Searching for freq inside loop allows frequencies to
            // be different for every temperature.
            // Would this ever occur?
#if 1
            // unsorted
            double closestFreq = 10000;
			for(unsigned i = 0; i < value->freq.size(); i++){
				if(closestFreq > abs(freq-value->freq.at(i))) {
					closestFreq = abs(freq-value->freq.at(i));
					tempvalues[j] = value->temp.at(i);
				}
			}
#else
            assert(std::is_sorted(value->freq.begin(),value->freq.end()));
            vector<double>::const_iterator igt = std::upper_bound(
                value->freq.begin()+1, value->freq.end()-1, freq);
            index = igt - value->freq.begin();
            double diff = fabs(freq - *igt);
            double diff_2 = fabs(freq - value->freq[index-1]);
            // Want temperature of closer frequency.
            if (diff < diff_2)
                tempvalues[j] = value->temp[index];
            else
                tempvalues[j] = value->temp[index-1];
#endif
        }
        if (freq < 1500 || vco == -1 || cap == -1) {
#if 1
            for (unsigned i = 1; i < pminfsp.size(); i++) {
				if (freq <= pminfsp.at(i)) {
					index = i - 1;
					break;
				}
            }
#else
            // Unsorted
            assert(std::is_sorted(pminfsp.begin(),pminfsp.end()));
            const vector<double>::const_iterator igt = std::upper_bound(
                pminfsp.begin()+1, pminfsp.end()-1, freq);
            // Original code for this always selected frequency BELOW
            // rather than closest, hence "begin()+1"
            index = igt - (pminfsp.begin()+1);
#endif
//            pminvalues[j] = pmax-value->calFunc.pmin.at(i-1).GetValue(freq);
        } else {
            /*
              index = freq>=1500 & freq<2310 & vco > 1; % covers vco 2 and 3, index 2
              index = freq>=2200 & freq<3000 & vco < 2; % covers vco 1 and 0, index 3
              index = freq>=3000 & freq<3800; % full range 3000-3800 covered, index 3
              index = freq>=3800 & freq<4000 & cap > 15; % vco 2 around 3680, should be high cap until about 3980, index 3
              index = freq>=3800 & freq<4580 & cap <=15; % covers remaining vco 2, index 4
              index = freq>=4470 & vco < 2; % covers vco 1 and 0 through 6 GHz, index 5
            */
            if (freq < 2310 && vco > 1)
//                pminvalues[j] = pmax-value->calFunc.pmin.at(2).GetValue(freq);
                index = 2;
            else if (freq >= 2200 && freq < 3000 && vco < 2)
//                pminvalues[j] = pmax-value->calFunc.pmin.at(3).GetValue(freq);
                index = 3;
            else if (freq >= 3000 && freq < 3600)
//                pminvalues[j] = pmax-value->calFunc.pmin.at(3).GetValue(freq);
                index = 3;
            else if (freq >= 3600 && freq < 3800 && vco == 3)
//                pminvalues[j] = pmax-value->calFunc.pmin.at(3).GetValue(freq);
                index = 3;
            else if (freq >= 3600 && freq < 4100 && vco == 2)
//                pminvalues[j] = pmax-value->calFunc.pmin.at(4).GetValue(freq);
                index = 4;
            else if (freq >= 4100 && freq < 4580 && cap <=15)
//                pminvalues[j] = pmax-value->calFunc.pmin.at(4).GetValue(freq);
                index = 4;
            else //freq >= 4470 && vco < 2
//                pminvalues[j] = pmax-value->calFunc.pmin.at(5).GetValue(freq);
                index = 5;
        }
        pminvalues[j] = pmax - value->calFunc.pmin[index].GetValue(freq);
        if(notEnoughValues)
            return pminvalues[j];
	}
	Pchip ret(tempvalues, pminvalues);
	return ret.GetValue(temp);
}
// powEst = (calFunc->attn.at(index).GetValue(i)-attn0) * (pmin-pmax)/(attn16383-attn0) + pmax;
unsigned binSearchPchip(const Pchip& pchp, double wantVal, double firstSub, double multiplier, double addition) {
	unsigned pdac = 8192;
	unsigned pdac_max = 16383;
	unsigned pdac_min = 0;
	double gotVal;
	double gotValMin = DBL_MIN;
	double gotValMax = DBL_MAX;
	for (;;) {
		gotVal = (pchp.GetValue((double)pdac) - firstSub)*multiplier + addition;
		if (gotVal <= wantVal) {
			pdac_max = pdac;
			gotValMax = gotVal;
		}
		else {
			pdac_min = pdac;
			gotValMin = gotVal;
		}
		if (pdac_max - pdac_min <= 1) {
			/*/ Two values not ending up equal due to /2 truncation
			if (pdac_min_in == pdac_min && DBL_MIN == gotValMin)
				gotValMin = pchp.GetValue((double)pdac_min);
			if (pdac_max_in == pdac_max && DBL_MAX == gotValMax)
				gotValMax = pchp.GetValue((double)pdac_max);
			//*/
			if (fabs(wantVal - gotValMin) < fabs(wantVal - gotValMax))
				return pdac_min;
			else
				return pdac_max;
		}
		pdac = (pdac_max + pdac_min) / 2;
	}
}
// 10000 offset:
// powEst = (calFunc->attn.at(index).GetValue(i)-attn0)/(attn0-attn10000) * (pmax-attnEst10000-offsetVal) + pmax;
// greater 10000 offset:
// powEst = (calFunc->attn.at(index).GetValue(i) - attn10000) / (attn10000 - attn13200) * (attnEst10000 - pmin + offsetVal) + attnEst10000 + offsetVal;
unsigned binSearchPchip(const Pchip& pchp, double wantVal, double firstSub, double multiplier, double addition, double offsetSub, double offsetMult, double offsetAdd) {
    unsigned pdac     = 8192;
    unsigned pdac_max = 16383;
    unsigned pdac_min = 0;
    double gotVal;
    double gotValMin = DBL_MIN;
    double gotValMax = DBL_MAX;
    for (;;) {
		if (pdac < 10000)
	        gotVal = (pchp.GetValue((double)pdac)-firstSub)*multiplier + addition;
		else
			gotVal = (pchp.GetValue((double)pdac)-offsetSub)*offsetMult + offsetAdd;
		
		if (gotVal < wantVal) {
            pdac_max = pdac;
            gotValMax = gotVal;
        } else {
            pdac_min = pdac;
            gotValMin = gotVal;
        }
        if (pdac_max - pdac_min <= 1) {
            /*/ Two values not ending up equal due to /2 truncation
            if (pdac_min_in == pdac_min && DBL_MIN == gotValMin)
                gotValMin = pchp.GetValue((double)pdac_min);
            if (pdac_max_in == pdac_max && DBL_MAX == gotValMax)
                gotValMax = pchp.GetValue((double)pdac_max);
			//*/
            if (fabs(wantVal - gotValMin) < fabs(wantVal - gotValMax))
                return pdac_min;
            else
                return pdac_max;
        }
        pdac = (pdac_max + pdac_min) / 2;
    }
}


//------------------------------------------------------------------------------------------------------------------------------
// GetPdacValue() - Temperature specific 
//------------------------------------------------------------------------------------------------------------------------------
vector<unsigned short> CalculateEstimates::GetPdacValue(double freq, double pow, double temp, double vco, double cap) {
	try{
		// The return value is array[0] = gain, array[1] = pdac
		vector<double> pdacvalues(values.size());
		vector<unsigned short> gainvalues(values.size());
		vector<double> tempvalues(values.size());
		MeasuredValues *value = NULL;
		int valueIndex = -1;
		PchipFunctions* calFunc = NULL;
		bool notEnoughValues = (values.size() <= 2); // return the normal value if there is only one temperature profile available.
		
		// If there are not enough values, then this figures out the closest temperature and only uses that to estimate
		if (notEnoughValues) {
            double closestFreq = 100000,closestTemp = 10000;
            for (unsigned j = 0; j < values.size(); j++) {
				value = &values.at(j);
				for (unsigned i = 0; i < value->freq.size(); i++){
					// after the first run, closest freq should be equal to closest for each additional MeasuredValue
					if (closestFreq >= abs(freq - value->freq.at(i))) {
						closestFreq = abs(freq - value->freq.at(i));
						// And then temperature should only change if the current value is closer than the previous
						if (closestTemp > abs(temp - value->temp.at(i))){
							closestTemp = abs(temp - value->temp.at(i));
							valueIndex = j;
						}
					}
				}
			}

			// if valueIndex doesn't change, something is wrong with temperatures, so run the normal getpdac function
			if (valueIndex == -1){
				const unsigned short tmp[2] = { 3000, 9 };
				return vector<unsigned short>(tmp, tmp + sizeof(tmp) / sizeof(tmp[0]));
			}
		}
		// Determine the upper and lower attn values 			
		double pmax = GetPmaxEstimate(freq, gain9, temp, vco, cap);
		double origPmax = pmax;
		/// @TODO GetPminEstimate calls GetPmaxEstimate --> huge duplication of effort?
		double pmin = GetPminEstimate(freq, temp, vco, cap);
		bool setPmax = false;
		// Scroll through all of the values and get the estimated pdac value and gain value for each. 
		for (unsigned j = 0; j < values.size(); j++) {
			if (notEnoughValues)
				value = &values.at(valueIndex);
			else
				value = &values.at(j);
			calFunc = &value->calFunc;

			// Get the temperature of the closest recorded frequency 
			int index = 0;
			double diff, diff_2;
#if 1
			// freqs not sorted
			double closestFreq = 10000;
			for (unsigned i = 0; i < value->freq.size(); i++){
				if (closestFreq > abs(freq - value->freq.at(i))) {
					closestFreq = abs(freq - value->freq.at(i));
					tempvalues[j] = value->temp.at(i);
				}
			}
#else
			// upper_bound finds value greater than requested.
			assert(std::is_sorted(value->freq.begin(), value->freq.end()));
			vector<double>::const_iterator igt = std::upper_bound(
				value->freq.begin() + 1, value->freq.end() - 1, freq);
			index = igt - value->freq.begin();
			diff = fabs(freq - *igt);
			diff_2 = fabs(freq - value->freq[index-1]);
			// Want temperature of closer frequency.
			if (diff < diff_2)
				tempvalues[j] = value->temp[index];
			else
				tempvalues[j] = value->temp[index-1];
#endif
			// Find both the upper and lower estimates for attn, save the difference from the current freq.
			if(freq >= value->attnFreq[value->attnFreq.size()-1]) {
				index = (int)value->attnFreq.size()-1;
				diff = -1;
			} else {
				assert(std::is_sorted(value->attnFreq.begin(), value->attnFreq.end()));
				vector<double>::const_iterator igt = std::upper_bound(
					value->attnFreq.begin() + 1, value->attnFreq.end() - 1, freq);
				index = (int)(igt - value->attnFreq.begin());
				diff = fabs(freq - *igt);
				diff_2 = fabs(freq - value->attnFreq[index - 1]);
			}
			

			double attn0   = calFunc->attn.at(index).GetValue(0);
			double attn0_2 = calFunc->attn.at(index-1).GetValue(0);
			bool singleEst = false; // If the second attn value is too far off, only use the closer values
			if (abs(origPmax - attn0) > 5 && abs(origPmax - attn0_2) < 5 && index > 1) {
				singleEst = true;
				index = index-1;
				attn0 = attn0_2;
			} else if (abs(origPmax - attn0_2) > 5 && abs(origPmax - attn0) < 5) {
				singleEst = true;
			}

			double attn16383    = calFunc->attn.at(index).GetValue(16383);
			double attn16383_2  = calFunc->attn.at(index-1).GetValue(16383);
			double attn10000   = calFunc->attn.at(index).GetValue(10000);
			double attn10000_2 = calFunc->attn.at(index-1).GetValue(10000);
			double attn13200, attn13200_2;
			if(value->card4122 == false) { // No need to get 3120 pdac estimate for 4122 
				if(freq < 1500) {
					attn13200 = calFunc->attn.at(index).GetValue(13200);
					attn13200_2 = calFunc->attn.at(index-1).GetValue(13200);
				} else {
					attn13200 = calFunc->attn.at(index).GetValue(12480);
					attn13200_2 = calFunc->attn.at(index-1).GetValue(12480);
				}
			}
			unsigned short gain = value->card4122 ? (freq>7800 ? 0 : 6) : 9;
			double attnEst10000, attnEst10000_2, offsetVal;
			bool offset = false;

			// Check to see if the intended power is greater than power at -9 gain setting
			if (pow > origPmax && value->card4122 == false) {
				if (setPmax == false) {
					pmax = GetPmaxEstimate(freq, gain0, temp, vco, cap);
					pmin = GetPmaxEstimate(freq, gain0attn, temp, vco, cap);
					setPmax = true;
				}
				attnEst10000   = (attn10000  -attn0)   * (pmin-pmax)/(attn13200  -attn0)   + pmax;
                attnEst10000_2 = (attn10000_2-attn0_2) * (pmin-pmax)/(attn13200_2-attn0_2) + pmax;
				gain = 0;
				offset = true;
						
				// Setting up the offset value based on frequency
				for (unsigned i = 1; i < fsp.size(); i++) {
					if(fsp.at(i) > 2300) {
						offsetVal = .4;
						break;
					}
					if(freq <= fsp.at(i)) {
						if(i == 1) {
							offsetVal = -.7/(fsp.at(i) - 75)*freq+.5+.7/(fsp.at(i)-75)*fsp.at(i);;
							break;
						} else if(fsp.at(i) < 1300) {
							offsetVal = -.8/(fsp.at(i) - fsp.at(i-1))*freq+.4+.8/(fsp.at(i)-fsp.at(i-1))*fsp.at(i);
							break;
						} else if(freq < 1500) {
							offsetVal = -.6/(fsp.at(i) - fsp.at(i-1))*freq+.28+.6/(fsp.at(i)-fsp.at(i-1))*fsp.at(i);
							break;
						} else if(freq < 2300) {
							offsetVal = .65;
							break;
						}
					}
				}
			}
			// save the gain value to the array
			gainvalues[j] = gain;

			// Continue if it's a max or min pdac case 
			if(pow > pmax) {
				pdacvalues[j] = 0;
				continue;
			}
			if(gain == 9 && pow < pmin) {
				pdacvalues[j] = 16383;
				continue;
			}
			if(value->card4122 == true && pow < pmin) {
				pdacvalues[j] = 16383;
				continue;
			}

			unsigned pdac_upper = ~0;
            unsigned pdac_lower = ~0;
            bool offset_upper = false;
            bool offset_lower = false;
            if (offset) {
                // Offset type 2 - adding a constant value
				pdac_upper = binSearchPchip(calFunc->attn[index], pow, attn0, (pmax - attnEst10000 - offsetVal)/(attn0 - attn10000),pmax,
					attn10000, (attnEst10000 - pmin + offsetVal)/(attn10000 - attn13200), attnEst10000+offsetVal);

				pdac_lower = binSearchPchip(calFunc->attn[index-1], pow, attn0_2, (pmax - attnEst10000_2 - offsetVal) / (attn0_2 - attn10000_2), pmax,
					attn10000_2, (attnEst10000_2 - pmin + offsetVal) / (attn10000_2 - attn13200_2), attnEst10000_2 + offsetVal);

            } else {
                // powEst = (calFunc->attn.at(index).GetValue(i)-attn0) * (pmin-pmax)/(attn16383-attn0) + pmax;
				pdac_upper = binSearchPchip(calFunc->attn[index], pow, attn0, (pmin - pmax) / (attn16383 - attn0), pmax);
                
				pdac_lower = binSearchPchip(calFunc->attn[index - 1], pow, attn0_2, (pmin - pmax) / (attn16383_2 - attn0_2), pmax);
            }
			double pdac;
			if (singleEst == true)
				pdac = pdac_upper;
			else
				pdac = (pdac_lower*diff + pdac_upper*diff_2) / (diff + diff_2);
            pdacvalues[j] = pdac;
#ifndef _NDEBUG
			double powEstUpp;
            double attn_upper = calFunc->attn.at(index).GetValue(pdac_upper);
            // Using final pdac with the coefficients for the upper values
            // gave a disturbing number of failures (some > 2dB) -->
            // trying a less ambitious test to check for self
            // consistency.
            if(offset) {
                // Offset type 2 - adding a constant value
                if(pdac_upper < 10000)
                    powEstUpp = (attn_upper-attn0)/(attn0-attn10000) * (pmax-attnEst10000-offsetVal) + pmax;
                else
                    powEstUpp = (attn_upper-attn10000)/(attn10000-attn13200) * (attnEst10000-pmin+offsetVal)+attnEst10000+offsetVal;
            } else {
                powEstUpp     = (attn_upper-attn0) * (pmin-pmax)/(attn16383-attn0) + pmax;
            }
            double pow_err_upp = powEstUpp-pow;
			double powEstLow;
            double attn_lower = calFunc->attn.at(index-1).GetValue(pdac_lower);
            if (offset) {
                if(pdac_lower < 10000)
                    powEstLow = (attn_lower-attn0_2)/(attn0_2-attn10000_2) * (pmax-attnEst10000_2-offsetVal) + pmax;
                else
                    powEstLow = (attn_lower-attn10000_2)/(attn10000_2-attn13200_2) * (attnEst10000_2-pmin+offsetVal)+attnEst10000_2+offsetVal;
            } else {
                powEstLow     = (attn_lower-attn0_2) * (pmin-pmax)/(attn16383_2-attn0_2) + pmax;
            }
            double pow_err_low = powEstLow-pow;
            if (fabs(pow_err_upp) > 1.0 || fabs(pow_err_low) > 1.0) {
                printf("Power Error (low,high) (%.2f, %.2f) at freq %.6f (%.0f, %.0f), pow %.2f, temp %f; pdac = %d (%d, %d)\n",
                       pow_err_upp,pow_err_low,freq, value->freq[index-1], value->freq[index], pow,temp, (unsigned)(pdac+0.5), pdac_lower, pdac_upper);
//                assert(pdac == 0 || pdac == 16383);
            }
#endif
        }
		if(notEnoughValues){
			const unsigned short tmp[2] = { (unsigned short)pdacvalues[0], (unsigned short)gainvalues[0] };
			return vector<unsigned short>(tmp, tmp + sizeof(tmp) / sizeof(tmp[0]));
		}
		Pchip ret(tempvalues, pdacvalues);
		
		const unsigned short tmp[2] = { (unsigned short)ret.GetValue(temp), (unsigned short)gainvalues[0] };
/// @TODO Could just return a struct:  Would hold the 2 value with labeled names and not call new/delete or require copying through intermediate array --> more efficient and easier to follow.
		return vector<unsigned short>(tmp, tmp + sizeof(tmp) / sizeof(tmp[0]));
		
	} catch(...) {
		const unsigned short tmp[2] = { 3000, 9 };
		return vector<unsigned short>(tmp, tmp + sizeof(tmp) / sizeof(tmp[0]));
	}
}

#pragma endregion 

