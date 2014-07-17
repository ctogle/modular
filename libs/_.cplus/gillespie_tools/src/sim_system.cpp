#include <iostream>
#include <vector>

#include "species.h"
#include "sim_system.h"

//using namespace std;

sim_system::sim_system ()
{
	total_captures = 0;
	capture_count = 0;
}

void sim_system::parse ()
{
	//std::vector<species> species_;
}

void sim_system::step ()
{
	printf("step\n");
	capture_count += 1;
}

void sim_system::run ()
{
	printf("run\n");
	while (capture_count < total_captures)
	{ 
		step();
	}
}

int sim_system::spill ()
{
	return 8;
}



void sim_system::run_test ()
{
	//cdef pySpecies[:] arrayview = specs
	//std::vector<species> species_(10);
	species species_[10];
	species sp;

	double val = 0;
	int kkk, ii1, ii2, ijk, i;

	for (kkk = 0; kkk < 10; kkk++)
	{
		for (ii1 = 0; ii1 < 10000; ii1++)
		{
			for (ii2 = 0; ii2 < 1000; ii2++)
			{
				for (ijk = 0; ijk < 10; ijk++)
				{
					sp = species_[ijk];
					sp.add_onee();
				}
			}
		}
		for (i = 0; i < 10; i++)
		{
			val += species_[ijk].get_onee();
		}
		printf("Value check\n");
		val = 0;
	}
}






int main ()
{
	sim_system sy;
	sy.run_test();
	return 0;
}

double addd(double val)
{
	return val + 1;
}

int maintwo ()
{
	double aaa = 0;
	int kkk, ii1, ii2, ijk;
	for (kkk = 0; kkk < 10; kkk++)
	{
		for (ii1 = 0; ii1 < 10000; ii1++)
		{
			for (ii2 = 0; ii2 < 1000; ii2++)
			{
				for (ijk = 0; ijk < 10; ijk++)
				{
					//aaa = aaa+1;
					aaa = addd(aaa);
				}
			}
		}
		printf("Value check\n");
	}
	return 0;
}



