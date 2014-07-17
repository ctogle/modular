
class sim_system
{
	public:
		sim_system ();

		int total_captures;
		int capture_count;

		void parse ();
		void step ();
		void run ();
		int spill ();


		void run_test (); /////////////////////
};

int main ();
int maintwo ();

