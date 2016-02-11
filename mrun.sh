#!/usr/bin/env bash

# usage:
# 1  ./mrun.sh 
# 2  ./mrun.sh <path/to/some.mcfg>
# 2  ./mrun.sh <path/to/some.mcfg> <number_of_processes>
# 3  ./mrun.sh <path/to/some.mcfg> --np <number_of_processes>
# 4  ./mrun.sh <path/to/some.mcfg> --mpi <path/to/some/hostfile>
# 5  for other mpi usages, simply combine mpiexec with usage case 2 in a separate script

PY_GOMODULE="modular4.mrun"

if [ $# -gt 2 ] ; then 
    if [ "$2" = "--mpi" ] ; then
        echo "mpi run using a hostfile"
        mpiexec --nooversubscribe --hostfile "$3" python -m "${PY_GOMODULE}" "$1"
    elif [ "$2" = "--np" ] ; then 
        echo "mpi run bound to this machine"
        mpiexec -n "$3" python -m "${PY_GOMODULE}" "$1"
    else
        echo "multicore run using serial submissions"
        python -m "${PY_GOMODULE}" "$1" "$2"
    fi
else python -m "${PY_GOMODULE}" "$@"
fi 

exit 0

