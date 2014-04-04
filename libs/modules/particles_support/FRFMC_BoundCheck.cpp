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
#include "FRFMC_Constants.h"
#include "FRFMC_BoundCheck.h"

#define PI 3.14159265358979323846264338327

using namespace std;

// Function for determining the change in cell index Deltai and Deltaj
// -- Returns the difference in cell index from CellNow and CellNext
void CellDifference(string CellNow, string CellNext, int& Deltai, int& Deltaj)
{
  // [1] DETERMINE THE INITIAL AND FINAL IJ LOCATIONS
  int inow=0,jnow=0,inext=0,jnext=0;
  InterpretIJ(CellNow,inow,jnow);
  InterpretIJ(CellNext,inext,jnext);
  // [1] END IJ LOCATION DETERMINATION
  // [2] CALCULATE DELTAI AND DELTAJ
  Deltai=inext-inow;
  Deltaj=jnext-jnow;
  // [2] CALCULATE DELTAI AND DELTAJ
  return;
}

// Function to determine the neutron's new position in a lateral or vertical only movement
// -- Returns the new XY location with shortest distance along the neutron's path to the next cell wall
void MoveNeutronLRUD(double XY[], double Theta, double D, int ArraySize, int inow, int jnow, int inext, int jnext, int Deltai, int Deltaj)
{
  double r=0.0;
// [1] CASE 1 -- THETA = [0,90]
  if((Theta>=0)&&(Theta<=90))
    {
      if(Deltaj==0)
	{ // For N/S change calculate ytilde the height of the triangle with r as the hypotenuse
	  double ytilde=D*(double)ArraySize-D*(double)inow-XY[1];
	  r=ytilde/sin(2.0*PI*Theta/360.0); // Get r from ytilde and theta
	  if(r<0.0)
	    {
	      r=-1.0*r;
	    }
	  XY[0]=XY[0]+r*cos(2.0*PI*Theta/360.0);
	  XY[1]=D*(double)ArraySize-D*(double)inow;
	}
      else{ // For W/E change calculate xtilde the width of the triangle with r as the hypotenuse
	double xtilde=D*(double)(jnow+1)-XY[0];
	r=xtilde/cos(2.0*PI*Theta/360.0); // Get r from xtilde and theta
	if(r<0.0)
	  {
	    r=-1.0*r;
	  }
	XY[0]=D*(double)(jnow+1); // Calculate and set the next XY location
	XY[1]=XY[1]+r*sin(2.0*PI*Theta/360.0);
      }
    }
// [2] CASE 2 -- THETA = [90,180]
  if((Theta>=90)&&(Theta<=180))
    {
      if(Deltaj==0)
	{ // For N/S change calculate ytilde the height of the triangle with r as the hypotenuse
	  double ytilde=D*(double)ArraySize-D*(double)inow-XY[1];
	  r=ytilde/sin((180.0-Theta)*2.0*PI/360.0); // Get r from ytilde and theta
	  if(r<0.0)
	    {
	      r=-1.0*r;
	    }
	  XY[0]=XY[0]+r*cos(2.0*PI*Theta/360.0); // Calculate and set the next XY location
	  XY[1]=D*(double)ArraySize-D*(double)inow;
	}
      else{ // For W/E change calculate xtilde the width of the triangle with r as the hypotenuse
	double xtilde=XY[0]-D*(double)jnow;
	r=xtilde/cos((180.0-Theta)*2.0*PI/360.0); // Get r from xtilde and theta
	if(r<0.0)
	  {
	    r=-1.0*r;
	  }
	XY[0]=D*(double)jnow; // Calculate and set the next XY location
	XY[1]=XY[1]+r*sin(2.0*PI*Theta/360.0);
      }
    }
// [3] CASE 3 -- THETA = [180,270]
  if((Theta>=180)&&(Theta<=270))
    {
      if(Deltaj==0)
	{ // For N/S change calculate ytilde the height of the triangle with r as the hypotenuse
	  double ytilde=XY[1]-(D*(double)ArraySize-D*(double)(inow+1));
	  r=ytilde/sin((Theta-180.0)*2.0*PI/360.0); // Get r from ytilde and theta
	  if(r<0.0)
	    {
	      r=-1.0*r;
	    }
	  XY[0]=XY[0]+r*cos(2.0*PI*Theta/360.0); // Calculate and set the next XY location
	  XY[1]=D*(double)ArraySize-D*(double)(inow+1);
	}
      else{ // For W/E change calculate xtilde the width of the triangle with r as the hypotenuse
	double xtilde=XY[0]-D*(double)jnow;
	r=xtilde/cos((Theta-180.0)*2.0*PI/360.0); // Get r from xtilde and theta
	if(r<0.0)
	  {
	    r=-1.0*r;
	  }
	XY[0]=D*(double)jnow; // Calculate and set the next XY location
	XY[1]=XY[1]+r*sin(2.0*PI*Theta/360.0);
      }
    }
// [4] CASE 4 -- THETA = [270,360]
  if((Theta>=270)&&(Theta<=360))
    {
      if(Deltaj==0)
	{ // For N/S change calculate ytilde the height of the triangle with r as the hypotenuse
	  double ytilde=XY[1]-(D*(double)ArraySize-D*(double)(inow+1));
	  r=ytilde/sin((360.0-Theta)*2.0*PI/360.0); // Get r from ytilde and theta
	  if(r<0.0)
	    {
	      r=-1.0*r;
	    }
	  XY[0]=XY[0]+r*cos(2.0*PI*Theta/360.0); // Calculate and set the next XY location
	  XY[1]=D*(double)ArraySize-D*(double)(inow+1);
	}
      else{ // For W/E change calculate xtilde the width of the triangle with r as the hypotenuse
	double xtilde=D*(double)(jnow+1)-XY[0];
	r=xtilde/cos((360.0-Theta)*2.0*PI/360.0); // Get r from xtilde and theta
	if(r<0.0)
	  {
	    r=-1.0*r;
	  }
	XY[0]=D*(double)(jnow+1); // Calculate and set the next XY location
	XY[1]=XY[1]+r*sin(2.0*PI*Theta/360.0);
      }
    }
  return;
}

/* Function for neutron movements where both deltai and deltaj are nonzero. We must calculate a xtilde
 and a ytilde and determine an r1 and r2. The r that is smallest tells us which neighbor the neutron
 hits first. We adjust the XY based on the sign of r1-r2 */
// -- Returns the new XY location of the neutron on the cell wall of the nearest neighbor
void MoveNeutronAll(double XY[], double Theta, double D, int ArraySize, int inow, int jnow, int inext, int jnext, int Deltai, int Deltaj)
{
// [1] CASE 1 -- THETA = [0,90]
  if((Theta>=0)&&(Theta<=90))
    {
      double xtilde=D*(double)(jnow+1)-XY[0];
      double ytilde=D*(double)(ArraySize)-D*(double)(inow)-XY[1];
      double r1=xtilde/cos(2.0*PI*Theta/360.0);
      double r2=ytilde/sin(2.0*PI*Theta/360.0);
      if(r1<r2)
	{ // r1 smaller indicates the X wall is hit first
	  XY[0]=D*(double)(jnow+1);
	  XY[1]=XY[1]+r1*sin(2.0*PI*Theta/360.0);
	}
      else{ // r2 smaller indicates the Y wall is hit first
	XY[0]=XY[0]+r2*cos(2.0*PI*Theta/360.0);
	XY[1]=D*(double)(ArraySize-inow);
      }
    }
// [2] CASE 2 -- THETA = [90,180]
  if((Theta>=90)&&(Theta<=180))
    {
      double xtilde=XY[0]-D*(double)jnow;
      double ytilde=D*(double)(ArraySize)-D*(double)(inow)-XY[1];
      double r1=xtilde/cos(2.0*PI*(180.0-Theta)/360.0);
      double r2=ytilde/sin(2.0*PI*(180.0-Theta)/360.0);
      if(r1<r2)
	{ // r1 smaller indicates the X wall is hit first
	  XY[0]=D*(double)jnow;
	  XY[1]=XY[1]+r1*sin(2.0*PI*Theta/360.0);
	}
      else{ // r2 smaller indicates the Y wall is hit first
	XY[0]=XY[0]+r2*cos(2.0*PI*Theta/360.0);
	XY[1]=D*(double)(ArraySize-inow);
      }
    }
// [3] CASE 3 -- THETA = [180,270]
  if((Theta>=180)&&(Theta<=270))
    {
      double xtilde=XY[0]-D*(double)jnow;
      double ytilde=XY[1]-(D*(double)ArraySize-D*(double)(inow+1));
      double r1=xtilde/cos(2.0*PI*(Theta-180.0)/360.0);
      double r2=ytilde/sin(2.0*PI*(Theta-180.0)/360.0);
      if(r1<r2)
	{ // r1 smaller indicates the X wall is hit first
	  XY[0]=D*(double)jnow;
	  XY[1]=XY[1]+r1*sin(2.0*PI*Theta/360.0);
	}
      else{ // r2 smaller indicates the Y wall is hit first
	XY[0]=XY[0]+r2*cos(2.0*PI*Theta/360.0);
	XY[1]=D*(double)ArraySize-D*(double)(inow+1);
      }
    }
  // [4] CASE 4 -- THETA = [270,360]
  if((Theta>=270)&&(Theta<=360))
    {
      double xtilde=D*(double)(jnow+1)-XY[0];
      double ytilde=XY[1]-(D*(double)ArraySize-D*(double)(inow+1));
      double r1=xtilde/cos(2.0*PI*(360.0-Theta)/360.0);
      double r2=ytilde/sin(2.0*PI*(360.0-Theta)/360.0);
      if(r1<r2)
	{ // r1 smaller indicates the X wall is hit first
	  XY[0]=D*(double)(jnow+1);
	  XY[1]=XY[1]+r1*sin(2.0*PI*Theta/360.0);
	}
      else{ // r2 smaller indicates the Y wall is hit first
	XY[0]=XY[0]+r2*cos(2.0*PI*Theta/360.0);
	XY[1]=D*(double)ArraySize-D*(double)(inow+1);
      }
    }
  return;
}

/* Primary function for checking boundaries. Calculates the difference in cell index and
 breaks this into 3 cases. BoundCheck then determines the closest boundary the neutron
 travels to and adjusts XY to this boundary */
// -- Returns the new XY location of the neutron on the cell wall of the nearest neighbor
int BoundCheck(double XY[], double R, double Theta, double D, int ArraySize, string CellNow, string CellNext)
{
  int Case=-2; // Initialize the Case to recalculation
  // [1] FIND THE IJ FOR NOW AND NEXT CELL
  int inow=0,jnow=0,inext=0,jnext=0;
  InterpretIJ(CellNow,inow,jnow);
  InterpretIJ(CellNext,inext,jnext);
  // [1] END FIND THE IJ FOR NOW AND NEXT CELL
  // [2] DETERMINE THE NUMBER OF CELLS THE NEUTRON IS ATTEMPTING TO TRAVERSE
  int Deltai=0,Deltaj=0;
  CellDifference(CellNow,CellNext,Deltai,Deltaj);
  // [2] END DETERMINE THE NUMBER OF CELLS THE NEUTRON IS ATTEMPTING TO TRAVERSE
  // [3] BREAK BOUNDCHECK INTO THREE POSSIBLE CASES
  // [3A] DELTAI!=0 && DELTAJ!=0 -- PARTICLE TRAVELLING BOTH WEST/EAST AND NORTH/SOUTH
  if((Deltai!=0)&&(Deltaj!=0))
    { // For vertical+horizontal neutron movement
      MoveNeutronAll(XY,Theta,D,ArraySize,inow,jnow,inext,jnext,Deltai,Deltaj);
      Case=-1;
      return Case;
    }
  else{ // [3B] EITHER DELTAI=0 OR DELTAJ=0
    // For only vertical or only horizontal neutron movement
    MoveNeutronLRUD(XY,Theta,D,ArraySize,inow,jnow,inext,jnext,Deltai,Deltaj);
    Case=-1;
    return Case;
  }
  return Case; // Should never get to this return
}


