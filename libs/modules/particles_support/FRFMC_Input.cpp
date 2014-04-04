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
#include <fstream>
#include <string>
#include <time.h>
#include "FRFMC_Input.h"

using namespace std;

/* The input file format is as follows:
 * C=#channels
 * A=A_11,A_12,...A_ic,A_21,...,A_2c,...,A_c1,...,A_cc
 * G=#generations
 * L=celllength
 * S=#generations to skip
 * E=epsilon
 * F=flux
 * 
 * Here, #channels indicates the size of the array [1,5], and the user indicates
 * which isotopes are where via the A input. The code reads from top to bottom and
 * from left to right in the array. The values for iso_ij should be the integer Z
 * (atomic mass) for the isotope in channel ij. For example for a 2x2 array with
 * U238 in the top left corner, U235 in the bottom right, Pu239 in the top right, 
 * and water in the lower left would look like:
 * 
 * A=238,239,18,235
 * 
 * The quantity #generations indicates the number of fission generations the user
 * requests as a minimum. The code will run until a relative error is reached as
 * well. Finally, celllength gives the physical size [cm] of the side of each cell
 * in the array. For example, L=10 for a 2x2 array would yield channels with each side
 * measuring 10cm so the total array is 20cm long. The last quantities are optional, but
 * help in preventing false convergences by skipping S generations before checking the
 * ratio of (KNow-KLast)/KLast. Epsilon is the accuracy criteria for a convergence of 
 * the fission rate. The flux parameter lets the user specify the starting neutron flux.
*/

// Function for determining the isotope from a given atomic mass
// -- Returns the isotope in string format
string AtoI(int A)
{
  string result="";
  switch (A)
    {
    case 18:
      result="H2O";
      break;
    case 235:
      result="U235";
      break;
    case 238:
      result="U238";
      break;
    case 239:
      result="PU239";
      break;
    }
  return result;
}

// Function for determining the runtime for FRFMC
// -- Returns the difference in the two clocked times
double RunTime(int FClock, int IClock)
{
  double TElapsed=(double)FClock-(double)IClock;
  return TElapsed;
}

// Function for reassigning the pointer arrays for the composition
// -- Returns the new array address for the isotopic composition
int ** AllocArray(ifstream& WIn, int ArraySize)
{
// [1] ACUIRE NEW TEMPARRAY
  // Create a temporary pointer to pointer
  int ** temparray = new int*[ArraySize];
  for(int i=0;i<ArraySize;i++)
    { // Assign the mxm elements to temparray
      temparray[i]=new int[ArraySize];
    }
  // Check that NumChannels is nonzero
  if(ArraySize==0)
    {
      cout<<"Input file must specify number of channels first"<<'\n';
      return temparray;
    }
  for(int x=0;x<ArraySize;x++)
    {
      for(int y=0;y<ArraySize;y++)
	{
	  WIn.ignore(1,'\n'); // Ignore the '=' or ','
	  WIn>>temparray[x][y];
	}
    }
// [1] END NEW TEMPARRAY ACQUISITION
// [2] TEMPARRAY CHECK
  for(int x=0;x<ArraySize;x++)
    {
      for(int y=0;y<ArraySize;y++)
	{
	  if((temparray[x][y]!=18)&&(temparray[x][y]!=235)&&(temparray[x][y]!=238)&&(temparray[x][y]!=239))
	    {
	      cout<<temparray[x][y]<<'\n';
	      cout<<"Isotope array is incomplete or contains unsupported isotopes"<<'\n';
	      return temparray; // **** DO SOME OTHER ERROR MESSAGE
	    }
	}
    }
// [2] END TEMPARRAY CHECK
// Return the temparry
  return temparray;
}

// Function for grabbing input integers from the input file (number of generations/channels)
// -- Returns the integer value from the input file
int GetInputInt(ifstream& WIn)
{
  // Initialize the input integer value IVal
  int IVal=0;
  WIn.ignore(1,'\n');
  WIn>>IVal;
  return IVal;
}

// Function for grabbing input doubles from the input file (physical length)
// -- Returns the double value from the input file
double GetInputDbl(ifstream& WIn)
{
  // Initialize the input double value DVal
  double DVal=0.0;
  WIn.ignore(1,'\n');
  WIn>>DVal;
  return DVal;
}

int GetFileName(int argc, char *argv[], string& InputName, ifstream& WIn)
{
  // Initialize an error call s for GetFName
  int s=0;
  int opt; // Option counter
  extern char *optarg; // Pointer to the option argument
  extern int optind,optopt,opterr;
  // Initialize the input file name InputName
  string InputFile="";
  while((opt=getopt(argc,argv,":h f:"))!=-1) // :h means -h requires no argument but f: means -f requires an argument
    {
      switch(opt)
	{
	case 'h': // Prints help information
	  cout<<'\n'<<"  A program designed to calculate the fission rates in individual channels for a user specified";
	  cout<<'\n'<<"  core geometry and composition. The program uses calculates the neutron flux through each";
	  cout<<'\n'<<"  channel and computes the fission rate based on the number of fissions in each generation and";
	  cout<<'\n'<<"  the time between fissions.";
	  cout<<'\n'<<"  To execute FRFMC type ./FRFMC -f filename.dat"<<'\n';
	  cout<<'\n'<<"  Where filename.dat is the input file in the following format:";
	  cout<<'\n'<<"  C=#channels";
	  cout<<'\n'<<"  A=A_11,A_12,...,A_iC,A_21,...,A_2C,...,A_C1,...,A_CC";
	  cout<<'\n'<<"  G=#generations";
	  cout<<'\n'<<"  L=rxlength";
	  cout<<'\n'<<"  C is the number of channels or size (m) of the mxm array";
	  cout<<'\n'<<"  A is the matrix of isotopic composition where A_11 begins in the top left corner of the core";
	  cout<<'\n'<<"  and proceeds left to right and top to bottom";
	  cout<<'\n'<<"  G is the minimum number of fission generations the user wants calculated";
	  cout<<'\n'<<"  L is the physical size of the detector in cm";
	  cout<<'\n'<<"  Contact pjaffke@vt.edu for questions/bugs..."<<'\n';
	  return -1;
	  break;
	case 'f': // Grab the input file name
	  InputFile=optarg;
	  cout<<"Your input file name is "<<InputFile<<'\n'; // Echo input file name
	  break;
	case ':':
	  cout<<'\n'<<"An input error occurred. Remember -f requires an argument. Please check input..."<<'\n';
	  return -1;
	  break;
	case '?':
	  cout<<'\n'<<"Option not recognized. Try -h for help"<<'\n';
	  return -1;
	  break;
	}
    }
  // Now that we have the input file name open this file
  if(InputFile!="")
    {
      WIn.open(InputFile.c_str());
      if(!WIn) // Check that WIn could open the file
	{
	  cout<<"Input file not found..."<<'\n';
	  return -1;
	}
      cout<<"Input file found!"<<'\n';
    }
  else{
    cout<<"No input file name provided..."<<'\n';
    return -1;
  }
  return s; // Return to main.cpp
}

