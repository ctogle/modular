#!/usr/bin/env bash

# usage:
# 1  ./mrun.sh 
# 2  ./mrun.sh --mcfg <path/to/some.mcfg>
# 3  ./mrun.sh --np <number_of_processes> --mcfg <path/to/some.mcfg>
# 4  ./mrun.sh --mpi <path/to/some/hostfile> --mcfg <path/to/some.mcfg>
# 5  for other mpi usages, simply combine mpiexec with usage case 2 in a separate script

PY_GOMODULE="modular4.mrun"

if [ $# -gt 1 ] ; then 
    if [ "$1" = "--mpi" ] ; then
        echo "mpi run using a hostfile"
        mpiexec --nooversubscribe --hostfile "$2" python -m "${PY_GOMODULE}" "$@"
    elif [ "$1" = "--np" ] ; then 
        echo "mpi run bound to this machine"
        mpiexec -n "$2" python -m "${PY_GOMODULE}" "$@"
    else
        python -m "${PY_GOMODULE}" "$@"
    fi
else python -m "${PY_GOMODULE}" "$@"
fi 

exit 0

