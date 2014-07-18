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
#include "FRFMC_Interaction.h"
#include "FRFMC_Constants.h"

#define PI 3.14159265358979323846264338327

using namespace std;

// Function for determining the type of interaction taking place
// -- Returns the interaction identifier {1,0,235,239}
int GetInteract(int inow, int jnow, int ** IsoArray, double E)
{
  // [1] DETERMINE INOWJNOW CELL COMPOSITION AND CROSS SECTIONS
  int A=IsoArray[inow][jnow];
  double SigmaS=FindXSEC(A,0,E); // Get the scattering cross section of isotope A at energy E
  double SigmaA=FindXSEC(A,1,E); // Get the absorption cross section of isotope A at energy E
  double SigmaF=FindXSEC(A,2,E); // Get the fission cross section of isotope A at energy E
  double AbsProb=(SigmaA+SigmaF)/(SigmaS+SigmaA+SigmaF);
  // [1] END DETERMINE INOWJNOW CELL COMPOSITION AND CROSS SECTIONS
  // [2] DISCRETE SAMPLE CROSS SECTIONS
  double eta1=GenRN();
  if(AbsProb>=eta1)
    { // If we have an absorption sample the absorption again for fission
      double eta2=GenRN();
      if((SigmaA/(SigmaF+SigmaA))>=eta2)
	{ // If we have an absorption again then return the absorption signal
	  return 0;
	}
      else{ // If we have a fission return the fission isotope (the fission signal)
	return A;
      }
    }
  else{ // If we had scattering send the scattering signal
    return 1;
  }  
  // [2] DISCRETE SAMPLE CROSS SECTIONS
}

// Function for elastic scattering calculation
// -- Returns the new Theta and E for elastic scattering
void ElasticScat(string CellNow, double& Theta, double& E, int ** IsoArray)
{
  double Ei=E; // Set initial energy
  int inow=0,jnow=0; // Acquire cell indices
  InterpretIJ(CellNow,inow,jnow);
  // [1] SAMPLE FINAL ENERGY
  int A=IsoArray[inow][jnow];
  double eta1=GenRN();
  double Ef=Ei*((1.0+pow((double)A,2.0)+2*(double)A*cos(2.0*PI*eta1))/(pow(1.0+(double)A,2.0)));
  // Set E to Ef
  E=Ef;
  // [2] SAMPLE SCATTERING ANGLE THETA_O
  double Theta_o=0.0;
  if(eta1>0.5)
    { // As ArcCos is degenerate for [0,PI] and [PI,2PI] we must manually apply the second half by splitting eta1 values
      Theta_o=(360.0-360.0*acos( (1.0+(double)A*cos(2.0*PI*eta1))/sqrt(1.0+pow((double)A,2.0)+2.0*(double)A*cos(2.0*PI*eta1)) ))/(2.0*PI);
    } // Theta_o is in degrees
  else{
    Theta_o=360.0*acos( (1.0+(double)A*cos(2.0*PI*eta1))/sqrt(1.0+pow((double)A,2.0)+2.0*(double)A*cos(2.0*PI*eta1)) )/(2.0*PI);
  } // Theta_o is in degrees
  // [3] SAMPLE PHI ANGLE
  double eta2=GenRN();
  double Phi_o=360.0*eta2; // In degrees
  // [4] SAMPLE THETA_F
  double Theta_f=(360.0*(acos(cos(Theta)*cos(Theta_o)+sqrt(1.0-pow(cos(Theta),2.0))*sqrt(1.0-pow(cos(Theta_o),2.0))*cos(Phi_o)) ))/(2.0*PI);
  double eta3=GenRN();
  // Theta_f is triply symmetric across eta1, eta2, and Theta so we sample for [0,PI] versus [PI,2PI]
  if(eta3>0.5)
    {
      Theta_f=360.0-Theta_f;
    }
  Theta=Theta_f; // Set new direction Theta=Theta_f
  return;
}

/* Main function to determine the nature of the interaction (elastic scattering, absorption or fission).
 If scattering occurs, CheckInteraction returns the new Theta and E. All interactions are returned with
 an interaction identifier {1,0,235,239} for {continuation(scattering),absorption,U235fission,Pu239fission} */
// -- Returns the interaction identifier above and, depending on the interaction, new neutron properties
int CheckInteraction(double& Theta, double& E, string CellNow, int ** IsoArray)
{
  int Type=1; // Initialize the type of interaction
  int inow=0,jnow=0; // Initialize the cell indices
  InterpretIJ(CellNow,inow,jnow); // Get the cell indices
  Type=GetInteract(inow,jnow,IsoArray,E);
  if(Type==1)
    { // If we had a scattering compute the new Theta and E
      ElasticScat(CellNow,Theta,E,IsoArray);
    }
  else{
    return Type;
  }
  return Type;
}




