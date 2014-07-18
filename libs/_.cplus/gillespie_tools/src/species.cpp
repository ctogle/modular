//#include <iostream>
#include "species.h"

//using namespace std;

species::species ()
{
	//initial_count = 0;
	//count = 0;

	onee = 0; /////////////////////
}

/*
species::species (int cnt)
{
	initial_count = cnt;
	count = cnt;

	onee = 0; /////////////////////
}

int species::get_count ()
{
	return count;
}

void species::set_count (int cnt)
{
	count = cnt;
}
*/


void species::add_onee ()/////////////////////////
{
	onee += 1;
}

double species::get_onee ()
{
	return onee;
}
