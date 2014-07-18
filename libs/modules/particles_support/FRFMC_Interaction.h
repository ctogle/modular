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

#ifndef INTERACTION_H
#define INTERACTION_H

#include <string>

using namespace std;

int GetInteract(int,int,int**,double);
void ElasticScat(string,double&,double&,int**);
int CheckInteraction(double&,double&,string,int**);

#endif /* INTERACTION_H */
