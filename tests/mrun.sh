
echo "performing mpirun of modular!"
#mpirun --nooversubscribe --hostfile ~/dev/hostfile modular.py correl_demo.mcfg
#mpirun --nooversubscribe --hostfile ~/dev/hostfile modular.py MM_kinetics_means.mcfg
mpirun --nooversubscribe --hostfile ~/dev/hostfile modular.py MM_kinetics_fitting.mcfg
echo "finished mpirun of modular!"



