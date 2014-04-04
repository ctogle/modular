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
#include "FRFMC_SetupSource.h"
#include "FRFMC_Fission.h"

using namespace std;

// Function to determine the number of fissile isotopes in the core
// -- Returns the int for the number of fissiles cells
int CountFissiles(int ArraySize, int ** IsoArray)
{
  int NumFissiles=0;
  int Fissile=0;
  // Run through the core counting the number of fissiles
  for(int i=0;i<ArraySize;i++)
    {
      for(int j=0;j<ArraySize;j++)
	{
	  Fissile=IsFissile(IsoArray[i][j]); // Returns 0 for non-fissiles and 1 for fissiles
	  NumFissiles=NumFissiles+Fissile; // Count the fissiles (1) or don't count the non-fissiles (0)
	}
    }
  return NumFissiles; // Return the number of fissiles counted
}

// Function to determine the source for the start of a generation calculation
// -- Returns the mxm array of the number of starting neutrons in each cell
int ** DetermineSource(int KLast, int ArraySize, int **IsoArray)
{
  // Initialize a temporary source array
  int **tempsource = new int*[ArraySize];
  for(int i=0;i<ArraySize;i++)
    {
      tempsource[i]=new int[ArraySize];
    }
  // Find the number of fissile cells
  int NFissile=CountFissiles(ArraySize,IsoArray);
  int NeuSum=0; // Counts the number of neutrons divied so far
  // Divide the number of neutrons in KLast evenly among these cells
  for(int i=0;i<ArraySize;i++)
    {
      for(int j=0;j<ArraySize;j++)
	{
	  // Place neutrons only in fissile cells
	  int TorF=IsFissile(IsoArray[i][j]);
	  if(TorF==1)
	    { // If cell is fissile fill with KLast/NFissile neutrons
	      tempsource[i][j]=int((double)KLast/(double)NFissile);
	      NeuSum=NeuSum+tempsource[i][j];
	    }
	  else{ // If cell is non-fissile fill with KLast/NFissile neutrons
	    tempsource[i][j]=0;
	  }
	}
    }
  // Calculate the remainder of neutrons and put them in the U235 cells
  int Remainder=KLast-NeuSum;
  for(int i=0;i<ArraySize;i++)
    {
      for(int j=0;j<ArraySize;j++)
	{
	  if(IsoArray[i][j]==235)
	    {
	      tempsource[i][j]=tempsource[i][j]+Remainder;
	      Remainder=0;
	      return tempsource; // Once we have divied out the remainder return the tempsource array
	    }
	}
    }
  if(Remainder!=0)
    { // If we have an only Pu239 core give the remaining neutrons to the Pu239 cells
      for(int i=0;i<ArraySize;i++)
	{
	  for(int j=0;j<ArraySize;j++)
	    {
	      if(IsoArray[i][j]==239)
		{
		  tempsource[i][j]=tempsource[i][j]+Remainder;
		  Remainder=0;
		  return tempsource; // Once we have divied out the remainder return the tempsource array
		}
	    }
	}    
    }
  return tempsource; // Return the tempsource array
}



