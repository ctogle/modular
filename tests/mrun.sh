
echo "performing mpirun of modular!"
mpirun -c 20 --nooversubscribe --hostfile ~/dev/hostfile modular.py correl_demo.mcfg
echo "finished mpirun of modular!"



