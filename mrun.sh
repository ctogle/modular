#!/usr/bin/env bash

# usage:
#   ./mrun.sh 
#   ./mrun.sh "path/to/some.mcfg"
#   ./mrun.sh "path/to/some.mcfg" mpi

PY_GOMODULE="modular4.mrun"

if [ "$2" = "mpi" ] ; then
    echo "performing mpirun of modular!"
    mpiexec --nooversubscribe --hostfile ~/dev/hostfile python -m "${PY_GOMODULE}" "$@"
    echo "finished mpirun of modular!"
else
    python -m "${PY_GOMODULE}" "$@"
fi



