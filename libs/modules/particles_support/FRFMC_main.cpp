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

 * The input file format is as follows:
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
 * 
 * This code is copyright (C) 2013, Patrick Jaffke, Virginia Tech Physics, pjaffke@vt.edu
 * 
 * To execute the code simply type ./FRFMC -f Input.dat where Input.dat follows
 * the above format and is in the same folder as FRFMC.
*/

#include "FRFMC_Input.h"
#include "FRFMC_Constants.h"
#include "FRFMC_Fission.h"
#include "FRFMC_SetupSource.h"
#include "FRFMC_CalcFate.h"
#include "FRFMC_BoundCheck.h"
#include "FRFMC_Interaction.h"

#include <stdlib.h>
#include <stdio.h>
#include <iostream>
#include <fstream>
#include <string>
#include <cmath>
#include <time.h>

#define PI 3.14159265358979323846264338327

using namespace std;

int main(int argc, char* argv[])
{
// [1] BEGIN PROBLEM SETUP
  // Start timer
  int t_initial=time(NULL);
  // Seed the random # generator
  srand(time(NULL));
  // Initialize the code-wide error call s
  int s=0;
  // Initialize array information
  int ArraySize=1; // The number of elements m in the mxm array
  int **IsoArray=new int*[ArraySize]; // The isotopic composition in each element
  for(int i=0;i<ArraySize;i++)
    { // Assign the mxm elements to IsoArray
      IsoArray[i]=new int[ArraySize];
    }
  double D=1.0; // The physical size of each cell
  int Fgen=100000; // Number of fission generations to run
  int GenSkip=0; // The number of generations to skip
  double epsilon=0.001; // The accuracy criteria for KCompare
  double Flux=2.0*1000000.0; // Starting flux of neutrons for generation 0
  string InputName=""; // Input file name
  ifstream WIn; // Input file stream
  ofstream WOut; // Output file stream
// [1A] COMPOSITION INITIALIZATION
  // We begin with an array full of H2O
  for(int i=0;i<ArraySize;i++)
    {
      for(int j=0;j<ArraySize;j++)
	{
	  IsoArray[i][j]=18; // Fill each channel with H2O
	}
    }
// [1A] END COMPOSITION INITIALIZATION
// [1B] BEGIN INPUT GRAB
  s=GetFileName(argc,argv,InputName,WIn);
  // GetOpt gets the input file name
  if(s<0)
    {
      return EXIT_FAILURE;
    }
  // [1B.1] INPUT FILE RIP
  char Probe;
  WIn>>Probe; // Get the first character of the input file
  while(!WIn.eof()) // Read the input file until the end of file is reached
    {
      switch(Probe)
	{
	case 'C': // For Probe=C get the number of channels
	  ArraySize=GetInputInt(WIn);
	  break;
	case 'A': // For Probe=A get the isotopic composition
	  IsoArray=AllocArray(WIn,ArraySize);
	  break;
	case 'G': // For Probe=G get the minimum number of generations
	  Fgen=GetInputInt(WIn);
	  break;
	case 'L': // For Probe=L get the physical length of each cell
	  D=GetInputDbl(WIn);
	  break;
	case 'S': // For Probe=S get the number of generations to skip
	  GenSkip=GetInputInt(WIn);
	  break;
	case 'E': // For Probe=E get the accuracy of KCompare
	  epsilon=GetInputDbl(WIn);
	  break;
	case 'F': // For Probe=F get the starting Flux
	  Flux=GetInputDbl(WIn);
	  break;
	}
      WIn.ignore(200,'\n'); // Jump to next line
      WIn>>Probe; // Get next header character
    }
  if(ArraySize>9)
    {
      cout<<"Code specifies an mxm matrix of isotopes where m<10"<<'\n';
      return EXIT_FAILURE;
    }
  WIn.close();
  // [1B.3] INPUT ECHO
  WOut.open("Results.dat");
  WOut<<"C="<<ArraySize<<'\n'<<"A=";
  for(int i=0;i<ArraySize;i++)
    {
      for(int j=0;j<ArraySize;j++)
	{
	  WOut<<IsoArray[i][j]<<',';
	}
    }
  WOut<<'\n'<<"G="<<Fgen<<'\n'<<"L="<<D<<'\n'<<"S="<<GenSkip<<'\n'<<"E="<<epsilon<<'\n'<<"F="<<Flux<<'\n'<<'\n';
  WOut<<"Problem Specifications:"<<'\n'<<ArraySize<<"x"<<ArraySize<<" array with a physical length of "<<(double)ArraySize*D<<" cm"<<'\n';
  WOut<<"Array composition is as follows:"<<'\n';
  for(int i=0;i<ArraySize;i++)
    {
      for(int j=0;j<ArraySize;j++)
	{
	  WOut<<AtoI(IsoArray[i][j])<<'\t';
	}
      WOut<<'\n';
    }
  WOut<<"FRFMC will run with a minimum of "<<Fgen<<" fission generations with optimal accuracy of "<<epsilon<<'\n';
  // [1B.3] END INPUT ECHO
// [2] BEGIN COMPUTATION
  WOut<<"Compiler RAND_MAX is "<<RAND_MAX<<'\n';
  // Create and initialize the number of fissions for U235 and Pu239 for generation i and the number of absorptions
  int **U235Fissions=new int*[ArraySize];
  int **Pu239Fissions=new int*[ArraySize];
  int **Absorptions=new int*[ArraySize];
  for(int i=0;i<ArraySize;i++)
    {
      U235Fissions[i]=new int[ArraySize];
      Pu239Fissions[i]=new int[ArraySize];
      Absorptions[i]=new int[ArraySize];
    }
  // Create and initialize the multiplication factors each generation Kgen and the current K for the generation running Kmade and the ratio KRatio
  int *Kgen=new int[Fgen]; // Holds the K (number of neutrons generated) for this generation
  Kgen[0]=Flux; // Begins with Flux neutrons
  int Kmade=Flux; // Holds the number of neutrons made in a generation
  double KRatio=0; // Holds the ratio we will compare to epsilon
  // Create and initialize the fission source term for neutrons 
  int **SourceNow=new int*[ArraySize];
  int **SourceLast=new int*[ArraySize];
  for(int i=0;i<ArraySize;i++)
    { // Assign the mxm elements to Source
      SourceNow[i]=new int[ArraySize];
      SourceLast[i]=new int[ArraySize];
    }
  // [2A.1] INITIALIZE GENERATION 0 SOURCE
  SourceLast=DetermineSource(Kgen[0],ArraySize,IsoArray); // Initialize generation i-1 neutron creation to generation i source
  WOut<<"Source distribution for initial generation is:"<<'\n';
  cout<<"Source distribution for initial generation is:"<<'\n';
  for(int i=0;i<ArraySize;i++)
    {
      for(int j=0;j<ArraySize;j++)
	{
	  cout<<SourceLast[i][j]<<'\t';
	  WOut<<SourceLast[i][j]<<'\t';
	}
      cout<<'\n';
      WOut<<'\n';
    }
  cout<<'\n';
  WOut<<'\n';
  // [2A.1] END GENERATION 0 SOURCE INITIALIZATION
  for(int gen=0;gen<Fgen;gen++)
    {
      // [2B] GENERATION INITIALIZATION
      SourceNow=DetermineSource(0,ArraySize,IsoArray); // Initialze generation i neutron creation to zero neutrons
      Kgen[gen]=Kmade; // Set KLast to number of neutrons just calculated for generation i-1
      Kmade=0; // Reset Kmade to the number of neutrons generated so far for generation i (0)
      for(int i=0;i<ArraySize;i++)
	{ // Reset the counter for the number of fissions for each isotope and the number of absorptions
	  for(int j=0;j<ArraySize;j++)
	    {
	      U235Fissions[i][j]=0;
	      Pu239Fissions[i][j]=0;
	      Absorptions[i][j]=0;
	    }
	}
      // [2B] END GENERATION INITIALIZATION
      // [2C] GENERATE HISTORY CELL BY CELL - BEGIN WITH CELL 00 AND WORK TOWARDS MM (LEFT TO RIGHT AND TOP TO BOTTOM)
      for(int i=0;i<ArraySize;i++)
	{
	  for(int j=0;j<ArraySize;j++)
	    {
	      int ncell=0;
	      while(ncell<SourceLast[i][j]) // Generate histories for all neutrons (SourceLast[i][j]) in cell ij
		{
		  cout<<"Starting neutron history in cell "<<i<<j<<'\n';
		  // [2D] PARTICLE INITIALIZATION
		  int A=18; // Isotope composition of initial cell ij -- Originally set to H2O
		  double E=0.0; // Initial energy E
		  double Theta=0.0; // Initial angle Theta
		  double XY[2]; // Initial particle XY location
		  for(int r=0;r<2;r++)
		    {
		      XY[r]=0.0;
		    }
		  int Fate=-2; // Initialize to a recalculation (-2)
		  PartStart(A,E,Theta,XY,i,j,D,ArraySize,IsoArray);
		  // PartStart determines the starting parameters for a particle
		  // [2D] END PARTICLE INITIALIZATION
		  Fate=CalcFate(A,E,Theta,XY,D,ArraySize,IsoArray);
		  // CalcFate returns {-1,0,235,239} for {escape,absorption,U235 fission,Pu239 fission}
		  // [2E] EXECUTE PARTICLE FATE
		  // Determine cell location
		  string CellID=FindCell(XY,ArraySize,D,Theta,0.0);
		  int icell=0,jcell=0; // Interpret CellID
		  InterpretIJ(CellID,icell,jcell);
		  int NumNeutrons=0; // Initialize the number of neutrons generated to zero
		  switch (Fate)
		    {
		    case 235: // Fate=235 means a U235 fission occurred
		      NumNeutrons=FissNeutrons(IsoArray[icell][jcell]); // Determine the number of neutrons generated in fission
		      // Add these neutrons to the new source
		      SourceNow[icell][jcell]=SourceNow[icell][jcell]+NumNeutrons;
		      // Add this fission to the U235 counter
		      U235Fissions[icell][jcell]++;
		      cout<<"U235 fission!"<<'\n';
		      break;
		    case 239: // Fate=239 means a Pu239 fission occurred
		      NumNeutrons=FissNeutrons(IsoArray[icell][jcell]); // Determine the number of neutrons generated in fission
		      // Add these neutrons to the new source
		      SourceNow[icell][jcell]=SourceNow[icell][jcell]+NumNeutrons;
		      // Add this fission to the Pu239 counter
		      Pu239Fissions[icell][jcell]++;
		      cout<<"Pu239 fission!"<<'\n';
		      break;
		    case 0: // Fate=0 means an absorption occurred
		      Absorptions[icell][jcell]++;
		      cout<<"Absorption!"<<'\n';
		      break;
		    case -1: // Fate=-1 means the neutron escaped
		      break;
		    case -2: // Fate=-2 means recalculate neutron history
		      ncell--;
		      break;
		    }
		  // [2E] END PARTICLE FATE EXECUTION
		  ncell++; // Proceed to next neutron in cell
		}
	      cout<<"Finished neutron history in cell "<<i<<j<<'\n';
	    }
	  cout<<"Finished neutron history in row "<<i<<'\n';
	}
      cout<<"Finished neutron history for generation "<<gen<<'\n';
      // [3] CALCULATE THE VALUE OF KMADE (NUMBER OF NEUTRONS PRODUCED IN GENERATION I)
      for(int i=0;i<ArraySize;i++)
	{
	  for(int j=0;j<ArraySize;j++)
	    {
	      Kmade=Kmade+SourceNow[i][j];
	    }
	}
      WOut<<'\n'<<"Generation "<<gen<<" produced "<<Kmade<<" neutrons"<<'\n';
      WOut<<"Generation "<<gen-1<<" produced "<<Kgen[gen]<<" neutrons"<<'\n';
      // [3B] CALCULATE THE RATIO OF KI AND KI-1 and KI-1 and KI-2 FOR GENERATIONS BEYOND 1
      if((gen>(GenSkip+1))&&(gen>1)) // If we have at least 3 generations and are past the GenSkip we can start calculating KRatio
	{
	  if(GenSkip!=0)
	    {
	      KRatio=KSkip(gen,GenSkip,Kgen,Kmade);
	    }
	  else{
	  // [3C] GET RATIO OF K FOR GEN I AND GEN I-1
	  KRatio = ((double)Kmade/(double)Kgen[gen] - (double)Kgen[gen]/(double)Kgen[gen-1])/((double)Kgen[gen]/(double)Kgen[gen-1]);
	  }
	  if(KRatio<0)
	    {
	      KRatio=-KRatio;
	    }
	  if(KRatio<epsilon)
	    { // Compare this KRatio with epsilon -- If it is small enough we can end the code
//	      Fgen=gen; ******COMMENTING OUT REMOVES EARLY CODE COMPLETION
	    }
	}
      // End code if Kmade = 0
      if(Kmade==0)
	{ // If generation i has produced no fission neutrons Kmade=0 and we must end the code
	  Fgen=gen;
	}
      // [4] ASSIGN NEXT GENERATION SOURCE
      cout<<"Current source will be set to next generation's starting source..."<<'\n';
      for(int i=0;i<ArraySize;i++)
	{
	  for(int j=0;j<ArraySize;j++)
	    {
	      SourceLast[i][j]=SourceNow[i][j];
	    }
	}
    }
// [5] DETERMINE THE NUMBER OF FISSIONS THAT OCCURRED IN THE GENERATION
  // Calculate the final time
  int t_final = time(NULL);
  double TElapsed=RunTime(t_final,t_initial);
  WOut<<"Computation required "<<TElapsed<<" seconds"<<'\n';
  WOut<<"After "<<Fgen<<" generations and Keff="<<(double)Kmade/(double)Kgen[Fgen]<<"..."<<'\n';
  WOut<<"Achieved results with epsilon="<<KRatio<<"..."<<'\n';
// [6] OUTPUT FISSION PROFILE
  WOut<<"U235 Fissions Profile:"<<'\n'<<'\n';
  for(int i=0;i<ArraySize;i++)
    {
      for(int j=0;j<ArraySize;j++)
	{
	  WOut<<U235Fissions[i][j]<<'\t';
	}
      WOut<<'\n';
    }
  WOut<<'\n'<<"Pu239 Fission Profile:"<<'\n'<<'\n';
  for(int i=0;i<ArraySize;i++)
    {
      for(int j=0;j<ArraySize;j++)
	{
	  WOut<<Pu239Fissions[i][j]<<'\t';
	}
      WOut<<'\n';
    }
  WOut<<'\n';
// [6] END OUTPUT FISSION PROFILE
// [7] OUTPUT ABSORPTION PROFILE
  WOut<<"Absorption Profile:"<<'\n'<<'\n';
  for(int i=0;i<ArraySize;i++)
    {
      for(int j=0;j<ArraySize;j++)
	{
	  WOut<<Absorptions[i][j]<<'\t';
	}
      WOut<<'\n';
    }
   WOut<<'\n'<<'\n';
// [7] OUTPUT ABSORPTION PROFILE
// [8] DEALLOCATE MEMORY
  for(int i=0;i<ArraySize;i++)
    {
      delete [] IsoArray[i];
      delete [] U235Fissions[i];
      delete [] Pu239Fissions[i];
      delete [] Absorptions[i];
      delete [] SourceNow[i];
      delete [] SourceLast[i];
    }
  delete [] IsoArray;
  delete [] U235Fissions;
  delete [] Pu239Fissions;
  delete [] Absorptions;
  delete [] SourceNow;
  delete [] SourceLast;
  delete [] Kgen;
  WOut.close();
  return EXIT_SUCCESS;
}


