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
#include <math.h>
#include <sstream>
#include "FRFMC_Constants.h"
#include "FRFMC_SetupSource.h"
#include "FRFMC_BoundCheck.h"
#include "FRFMC_Interaction.h"
#include "FRFMC_CalcFate.h"

#define PI 3.14159265358979323846264338327

using namespace std;

/* Function for finding the cell the particle is travelling TOWARDS (i.e. finding new cell for an initial
 position XY with a vector R and direction Theta or finding current cell if R=0) */
// -- Returns the string of the cell the particle is travelling TOWARDS ij so "ab" means i=a j=b
// -- A value of i=-1 indicates the southern exterior of the core while j=-1 indicates the western exterior
string FindCell(double XY[], int ArraySize, double D, double Theta, double R)
{
  // NOTE** Setting R=0.0 determines the current cell id
  string ij="";
  cout<<"Initial position is {"<<XY[0]<<","<<XY[1]<<"} with directional angle theta="<<Theta<<" and vector R="<<R<<'\n';
  double XFinal=XY[0]+R*cos(2.0*PI*Theta/360.0);
  double YFinal=XY[1]+R*sin(2.0*PI*Theta/360.0);
  double XYFinal[2];
  XYFinal[0]=XFinal;
  XYFinal[1]=YFinal;
  cout<<"Final position would be {"<<XYFinal[0]<<","<<XYFinal[1]<<"} with directional angle theta="<<Theta;
// [1] LOCATE PARTICLE AND TRIGGER FOR ON-WALL PARTICLES
  int icell=0,jcell=0; // Initialize the cell locations
  int xwalltrig=0,ywalltrig=0; // Triggers to indicate if the particle is on a cell wall
  for(int i=ArraySize-1;i>=0;i--) // Search for icell from bottom to top (i=ArraySize-1 to i=0)
    {
      if(((D*(double)(ArraySize-1-i))<=XYFinal[1])&&(XYFinal[1]<=(D*(double)(ArraySize-i))))
	{ // When the Y value falls into the range (i-1)*cellsize<=Y<=(i)*cellsize we have found the particle
	  icell=i;
	  // [1A.1] ON Y-WALL TRIGGER
	  if((XYFinal[1]==D*(double)(ArraySize-1-i))||(XYFinal[1]==D*(double)(ArraySize-i)))
	    { // Check if particle is on the y-cell wall
	      ywalltrig=1;
	    }
	  // [1A.1] END ON Y-WALL TRIGGER
	  break;
	}
    }
  // [1A.2] CHECK IF PARTICLE HAS LEFT CORE
  if(XYFinal[1]>D*(double)ArraySize)
    { // Particles above y=D*ArraySize are north of the core i=-1
      icell=-1;
    }
  if(XYFinal[1]<0.0)
    { // Particles below y=0 are south of the core i=ArraySize
      icell=ArraySize;
    }
  // [1A.2] END CORE ABANDONEMENT CHECK
  for(int j=0;j<ArraySize;j++) // Search for jcell from left to right (j=0 to j=ArraySize-1)
    {
      if(((D*(double)j)<=XYFinal[0])&&(XYFinal[0]<=(D*(double)(j+1))))
	{ // When the X value falls into the range (j)*cellsize<=X<=(j+1)*cellsize we have found the particle
	  jcell=j;
	  // [1B.1] ON X-WALL TRIGGER
	  if((XYFinal[0]==D*(double)j)||(XYFinal[0]==D*(double)(j+1)))
	    { // Check if particle is on the x cell wall
	      xwalltrig=1;
	    }
	  // [1B.1] END ON X-WALL TRIGGER
	  break;
	}
    }
  // [1B.2] CHECK IF PARTICLE HAS LEFT CORE
  if(XYFinal[0]>D*(double)ArraySize)
    { // Particles above x=D*ArraySize are east of the core j=ArraySize
      jcell=ArraySize;
    }
  if(XYFinal[0]<0.0)
    { // Particles below x=0 are west of the core j=-1
      jcell=-1;
    }
  // [1B.2] END CORE ABANDONEMENT CHECK
// [1] END PARTICLE LOCATE

// [2] DETERMINE TRAVEL LOCATION BASED ON DIRECTION (THETA)
  if(ywalltrig!=0)
    {
      if(XYFinal[1]==0)
	{ // Particles on x-axis can travel into region ArraySize (below core)
	  icell=icell+1;
	}
      if(sin(2.0*PI*Theta/360.0)>=0) // Convert theta to radians
	{ // If particle is travelling north (sin(theta)>=0) reduce cell index
	  icell=icell-1;
	}
    }
  if(xwalltrig!=0)
    {
      if(XYFinal[0]==0)
	{ // Particles on y-axis can travel into region -1 (left of core)
	  jcell=jcell-1;
	}
      if(cos(2.0*PI*Theta/360.0)>=0) // Convert theta to radians
	{ // If particle is travelling east (cos(theta)>=0) increase cell index
	  jcell=jcell+1;
	}
    }
// [2] END TRAVEL LOCATION DETERMINATION
// [3] CONVERT CELL INDICES INTO A STRING IJ
  stringstream iStream; (stringstream:: in | stringstream:: out);
  stringstream jStream; (stringstream:: in | stringstream:: out);
  string Temp="";
  iStream<<icell; // Input icell index
  iStream>>Temp;
  ij+=Temp; // Append to ij
  Temp="";
  jStream<<jcell; // Input jcell index
  jStream>>Temp;
  ij+=Temp; // Append to ij
  cout<<" in cell "<<ij<<'\n';
  return ij; // Return ij
// [3] END CELL INDEX CONVERSION
}

// Function to determine if the particle has left the core region (i.e. is i/j either -1 or ArraySize)
// -- Returns {1,-1} for a {check interaction,escape} fate
int CheckFate(string CellNow, int ArraySize)
{
  // [1] ACQUIRE THE NEW I AND J CELL INDICES
  int inew=0,jnew=0;
  InterpretIJ(CellNow,inew,jnew);
  // [1] ACQUIRE THE NEW I AND J CELL INDICES
  // [2] CHECK THE I AND J CELL INDICES
  if((inew==ArraySize)||(inew==-1)||(jnew==ArraySize)||(jnew==-1))
    { // If the cell indices state that i=ArraySize (south of core), i=-1 (north of core), j=ArraySize (east of core), or j=-1 (west of core)
      return -1; // Return escape signal
    }
  else{ // If the neutron is still in the core return a signal to check for interactions
    return 1;
  }
  // [2] CHECK THE I AND J CELL INDICES
}

// Function for calculating the pathlength vector R based on the cell and isotope in that cell
// -- Returns the value for the vector R
double CalcR(string Cell, double E, int** IsoArray)
{
  double R=0.0;
  // [1] FIND IJ FOR THIS CELLID
  int i=0,j=0;
  InterpretIJ(Cell,i,j);
  // [1] END IJ FINDING
  // [2] ACQUIRE TOTAL XSEC FOR THIS CELLID
  int A=IsoArray[i][j]; // Get the atomic mass of this cell
  double SigmaS=FindXSEC(A,0,E); // Get the scattering cross section of isotope A at energy E
  double SigmaA=FindXSEC(A,1,E); // Get the absorption cross section of isotope A at energy E
  double SigmaF=FindXSEC(A,2,E); // Get the fission cross section of isotope A at energy E
  double SigmaTot=SigmaS+SigmaA+SigmaF; // Sum for the total cross section of isotope A at energy E
  // [2] END TOTAL XSEC ACQUISTION
  // [3] GENERATE PATHLENGTH R -- r = -ln[eta]/SigmaTot
  double eta=GenRN();
  R=-log(eta)/SigmaTot;
  // [3] END PATHLENGTH GENERATION
  return R;
}

/* Primary function for neutron history calculation. Follows the neutron as it undergoes scattering, absorption,
 or fission. The neutron can also leave the core in which case the fate is escape. */
// -- Returns the fate as well as the final location XY, energy E, and direction Theta
// Fate = {-1,0,235,239} where {escape,absorption,U235fission,Pu239fission}
int CalcFate(int& A, double& E, double& Theta, double XY[], double D, int ArraySize, int** IsoArray)
{
  // [1] INITIALIZE THE NEUTRON PATH
  int End=1; // Initialize an ending trigger End
  double R=0.0;  // Initialize the pathlength
  string CellNow=FindCell(XY,ArraySize,D,Theta,0.0);  // Locate the cell id first
  R=CalcR(CellNow,E,IsoArray);  // Calculate the pathlength vector R
  // [1] END NEUTRINO PATH INITIALIZATION
  while(End==1) //****//
    {
      // [2] FIND NEW XY LOCATION OF NEUTRON
      // [2A] CHECK IF NEUTRON LEFT CURRENT CELL
      string CellNext=FindCell(XY,ArraySize,D,Theta,R); // Find next cell with the vector R as calculated above
      if(CellNow==CellNext)
	{ // If neutron is still in current cell accept new x and y position
	  XY[0]=XY[0]+R*cos(2.0*PI*Theta/360.0);
	  XY[1]=XY[1]+R*sin(2.0*PI*Theta/360.0);
	  CellNow=CellNext;
	}
      // [2A] END NEUTRON LEAVE CHECK
      else{
	// [2B] NEUTRONS LEAVING THE CURRENT CELL MUST BE CLEARED BY CHECKBOUNDS
	cout<<"BoundCheck will clear the neutron"<<'\n';
	int CBR=BoundCheck(XY,R,Theta,D,ArraySize,CellNow,CellNext);
	// BoundCheck has now altered the XY position to a cell wall
	CellNow=FindCell(XY,ArraySize,D,Theta,0); // Set the current cell CellNow to the new XY location
	if(CBR==-2)
	  { // If BoundCheck sends an error recalculate the neutron history
	    return -2;
	  }
	// [2B] END CHECKBOUNDS CLEARANCE
	// [2C] CHECK FATE OF NEUTRON
	End=CheckFate(CellNow,ArraySize);
	// CheckFate returns 1 for a continuation (check for interactions) or -1 for an escape
	if(End==-1)
	  {
	    return End; // Send escape signal
	  }
	// [2C] EBD CHECK FATE OF NEUTRON
	// [2D] RECALCULATE NEUTRON PATHLENGTH IF BOUNDCHECK REQUIRES
	if(CBR==-1)
	  {
	    cout<<"CheckBounds requires a recalculation of the pathlength"<<'\n';
	    R=CalcR(CellNow,E,IsoArray);
	    cout<<"New vector is R="<<R<<'\n';
	    continue; // Return back to //****// and restart the cycle
	  }
	// [2D] END RECALCULATION OF PATHLENGTH
      }
      // [2] END NEW XY LOCATION SEARCH
      // [3] CHECK NEUTRON INTERACTIONS
      cout<<"CheckBounds asks for neutron interaction check"<<'\n';
      int CIR=CheckInteraction(Theta,E,CellNow,IsoArray);
      // CheckInteraction has changed Mu and E, or an absorption/fission has occurred {1,0,235,239} for {continuation,absorption,U235fission,Pu239fission}
      if(CIR==0)
	{
	  return 0; // Return absorption signal
	}
      if(CIR==235)
	{
	  return 235; // Return U235 fission signal
	}
      if(CIR==239)
	{
	  return 239; // Return Pu239 fission signal
	}
      // [3] END NEUTRON INTERACTION CHECK
      // [4] CALCULATE NEXT R WITH NEW THETA
      // If CIR returns 1 continue neutron history
      CellNow=FindCell(XY,ArraySize,D,Theta,0); // Reevaluate cell id with new theta
      cout<<"CIR returns scattering with theta="<<Theta<<" and E="<<E<<'\n';
      R=CalcR(CellNow,E,IsoArray);
      // [4] END RECALCULATION WITH NEW R AND THETA
      // Return back to //****// and restart the cycle
    }
  return End; // Should never get to this point
}



