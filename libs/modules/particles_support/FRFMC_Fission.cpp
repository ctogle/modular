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
#include "FRFMC_CalcFate.h"
#include "FRFMC_Fission.h"

using namespace std;

// Create a list of the energy bins [MeV] for the U235 and Pu239 fission energy spectrum
double U235EB[42]={0.0, 0.1499844, 0.243998, 0.3266870, 0.4037596, 0.4775756, 0.5494156,
		   0.62008668, 0.69015342, 0.7600414, 0.8300941, 0.9006028, 0.9718277,
		   1.0440105, 1.1173842, 1.1921801, 1.2686347, 1.3469958, 1.4275276,
		   1.51051695, 1.5962805, 1.6851732, 1.7775975, 1.8740158, 1.974966,
		   2.0810820, 2.1931215, 2.3120025, 2.4388555, 2.5750965, 2.7225375,
		   2.8835515, 3.0613375, 3.260357, 3.487113, 3.751636, 4.070634,
		   4.475229, 5.0347429, 5.967952, 14.9822, 14.9822};
double Pu239EB[42]={0.0, 0.1521257, 0.248035, 0.332732, 0.411955, 0.4880771, 0.5623875,
		    0.635702, 0.7085932, 0.781497, 0.854767, 0.928707, 1.0035905,
		    1.0796742, 1.1572087, 1.2364446, 1.3176412, 1.401071, 1.4870275,
		    1.575831, 1.667837, 1.763445, 1.8631101, 1.9673565, 2.0767961,
		    2.192152, 2.3142894, 2.4442591, 2.5833574, 2.7332117, 2.89590779,
		    3.0741806, 3.2717242, 3.4937014, 3.7476508, 4.0452240, 4.4058775,
		    4.8659414, 5.506595, 6.584995, 14.9822, 14.9822};
// Using the function N235[E]=0.433Exp[-1.036E]Sinh[\sqrt{2.29E}] and N239[E]=0.6739\sqrt{E}Exp[-E/1.41] from "Improved Formula for Prompt Fission Neutron Spectrum" by Aziz et al. and 20 energy bins

#define PI 3.14159265358979323846264338327

// Function to determine if an isotope in the isotope array is fissile
// -- Returns a 0 for false (non-fissile) and a 1 for true (fissile)
int IsFissile(int Iso)
{
  int result=0;
  if((Iso==235)||(Iso==239))
    {
      result=1;
    }
  return result;
}

// Function for returning the energy for a fission
// -- Returns the fission energy for an input in [MeV]
double FissE(int A)
{
  double E=0.0; // Initialize energy
  int J=40; // Number of energy bins
  double eta1=GenRN(); // Generate random number eta1
  int j=(int)(floor(eta1*(double)J)); // j runs from [0,19]
  double eta2=GenRN(); // Generate random number eta2
  if(A==235)
    { // For U235 sample from U235 above
      E=U235EB[j]+eta2*(U235EB[j+1]-U235EB[j]);
    }
  if(A==239)
    { // For Pu239 sample from Pu239 above
      E=Pu239EB[j]+eta2*(Pu239EB[j+1]-Pu239EB[j]);
    }
  return E;
}

// Function for returning the number of fission neutrons produced
// -- Returns the number of fission neutrons generated
int FissNeutrons(int A)
{
  double etaT[2]={2.065,2.035};
  int Iso=3;
  switch (A)
    {
    case 235:
      Iso=0;
      break;
    case 239:
      Iso=1;
      break;
    }
  if(Iso==3)
    { // We are trying to fission something other than U235 or Pu239
      return -1;
    }
  double Compare=etaT[Iso]-(int)etaT[Iso];
  double eta=GenRN();
  if(eta<=Compare)
    {
      return (int)etaT[Iso]+1;
    }
  else{
    return (int)etaT[Iso];
  }
}

// Function for determining the initial direction of the fission neutrons
// -- Returns an angle for the neutron in degrees
double FissTheta()
{
  // Generate a random number and determine the angle via 2pi*eta
  double angle=0.0;
  double eta=GenRN();
  angle=2.0*PI*eta;
  return angle;
}

// Function for running through the particle preparation for a neutron generation
// -- Returns the initial isotopic composition, energy, direction, and XY location
void PartStart(int& A, double& E, double& Theta, double XY[], int i, int j, double D, int ArraySize, int ** IsoArray)
{
  A=IsoArray[i][j]; // Set initial isotopic composition
  int FissTF=IsFissile(A);
  if(FissTF==1)
    {
      E=FissE(A);
    }
  else{
    E=0.0; // Error we shouldn't be generating neutrons in a non-fissile environment
  }
  Theta=FissTheta(); // Returns Theta in degrees
  // Begin the neutrons in the center of the cell ij
  XY[0]=D/2.0+D*(double)j;
  XY[1]=D*(double)ArraySize-D/2.0-D*(double)i;
  return;
}

// Function for going through the fission sequence
// -- Adds the new fission neutrons to this generation's neutron production SourceNew
void FissionSequence(double XY[], double& Theta, double D, int ArraySize, int ** SourceNew, int ** IsoArray)
{
  // Locate the cell the fission is occurring in
  string CellID=FindCell(XY,ArraySize,D,Theta,0);
  int i=0,j=0; // Interpret CellID
  InterpretIJ(CellID,i,j);
  int NumNeutrons=FissNeutrons(IsoArray[i][j]); // Determine the number of neutrons generated in fission
  // Add these neutrons to the new source
  SourceNew[i][j]=SourceNew[i][j]+NumNeutrons;
  return;
}

