/* Monte Carlo Class - Final Project: We wish to calculate the fission rates inside
 * a given fuel element array. We allow the user to specify the array size and the
 * composition of each fuel channel. For this project, we keep the array sizing
 * below 5 channels, but the physical size is up to the user. The user can define
 * the channels to contain U235, U238, Pu239, or water. The code is meant to simulate
 * a pool-type research reactor with fission channels and will return the fission
 * rates for the fissile isotopes as well as the neutron flux outside the reactor
 * as a means to estimate neutron background.

 * The code begins by taking in the user-specified geometry. Our program comes hard-
 * wired with cross-sections for the various isotopes and water. We consider several
 * interaction processes. First, we are using an energy-dependent cross-section so we
 * split the neutron energies into either thermal or super-thermal for evaluating an
 * interaction type. We consider absorption, scattering (elastic), and
 * fission (for the fissiles). Any fission is tallied for the particular isotope
 * and we will produce an overall fission rate at the end of the code.

 * This code is copyright (C) 2013, Patrick Jaffke, Virginia Tech Physics, pjaffke@vt.edu
*/

#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <string>
#include <cmath>
#include "FRFMC_Constants.h"

using namespace std;

double OG[4]={0.03343,0.000240235,0.04833,0.000240235}; // ORIGINAL** Atom densities for the four isotopes {H2O,U235,U238,Pu239}

// Cross section lists for {H2O, U235, U238, Pu239} in barns for {Scat, Abs, Fiss}
double ThermalXSec[4][3]={{103.0,0.664,0.0},{15.04,683.21,584.4},{9.360,2.717,0.0},{7.968,1017.7,747.7}};
double FastXSec[4][3]={{10.591,0.0001735,0.0},{4.566,2.056,2.056},{4.804,1.13794,1.136},{2.984,2.338,2.338}};
// TXSec from Kaeri (Korean Atomic Energy Research Institute) and H2O from "Introduction to Nuclear Engineering" by Lamarsh J. and Baratta A.
// FXSec from Kaeri (Korean Atomic Energy Research Institute) @ fission spectrum average energy H2O = 2sigma_h + sigma_o for fast xsec

// Function for returning the cross section for a given isotope and interaction type (0,1,2) means (scattering,absorption,fission)
// -- Returns the cross section in b
double FindXSEC(int A, int IntType, double E)
{
  double N[4]={0.03343,0.240235,0.04833,0.240235}; // TESTING** Atom densities for the four isotopes {H2O,U235,U238,Pu239}
  double sigma=0.0;
  // [1] TRANSLATE A INTO INDEX I
  int I=0;
  switch (A)
    {
    case 18:
      I=0;
      break;
    case 235:
      I=1;
      break;
    case 238:
      I=2;
      break;
    case 239:
      I=3;
      break;
    }
  // [2] GRAB CROSS SECTION FROM XSECLIST
  if(E<=0.025/1000000) // Thermal energies in [MeV]
    {
      sigma=ThermalXSec[I][IntType]*N[I];
    }
  else{ // Fast energies
    sigma=FastXSec[I][IntType]*N[I];
  }
  return sigma;
}

// Function for finding a random variable eta
// -- Returns a random variable eta
double GenRN()
{
  // [1] GENERATE RANDOM NUMBER AND NORMALIZE TO [0,1]
  double RN=(double)rand() / ((double)RAND_MAX+0.0);
  return RN;
}

// Function for interpreting the cell index
// -- Returns the i and j components for a cell index
void InterpretIJ(string CellID, int& i, int& j)
{
  // Determine length of CellID string
  int len=CellID.size();
  int itrig=0,jtrig=0; // Set to 1 when we've determined what i or j is
  int minusspot=0; // Tag for determining where a minus sign is
  switch (len)
    {
    case 4: // For this case we know the cell id is -1-1
      i=-1;
      j=-1;
      break;
    case 3: // For this case we know one cell id is -1 so it is -1n or n-1 -- Determine minusspot
      for(int a=0;a<3;a++)
	{ // Loops through the string
	  if(CellID[a]=='-')
	    {
	      minusspot=a; // Locate where this minus sign is
	    }
	}
      if(minusspot==0)
	{
	  i=-(CellID[1]-48); // -48 converts the ASCII number to the actual int
	  j=CellID[2]-48;
	}
      else{
	i=CellID[0]-48;
	j=-(CellID[2]-48); // j is the negative index
      }
      break;
    case 2: // For this case the first char is the i index and the second char is the j index
      i=CellID[0]-48;
      j=CellID[1]-48;
      break;
    }
  return;
}

// Function for calculating the cumulative K values KSkip when we skip generations
// -- Returns the double for the value of K_c^(gen)
double KSkip(int gen, int GenSkip, int Kgen[], int Kmade)
{
  double Val1=0.0;
  for(int g=GenSkip;g<gen-1;g++)
    {
      Val1=Val1+(double)Kgen[g+1]/(double)Kgen[g];
    }
  Val1=Val1/(double)(gen-GenSkip);
  double Val2=0.0;
    for(int g=GenSkip;g<gen-2;g++)
    {
      Val1=Val1+(double)Kgen[g+1]/(double)Kgen[g];
    }
  Val1=Val1/(double)(gen-1-GenSkip);
  double KRatio=(Val1-Val2)/Val2;
  return KRatio; 
}



