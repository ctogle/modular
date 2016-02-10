#!/usr/bin/env bash

# usage:
# 1  ./mrun.sh 
# 2  ./mrun.sh <path/to/some.mcfg>
# 3  ./mrun.sh <path/to/some.mcfg> --np <number_of_processes>
# 4  ./mrun.sh <path/to/some.mcfg> --mpi <path/to/some/hostfile>
# 5  for other mpi usages, simply combine mpiexec with usage case 2 in a separate script

PY_GOMODULE="modular4.mrun"

while test $# -gt 0
do
    case "$2" in
        --mpi) mpiexec --nooversubscribe --hostfile "$3" python -m "${PY_GOMODULE}" "$@"
            ;;
        --np) mpiexec -n "$3" python -m "${PY_GOMODULE}" "$@"
            ;;
        *) python -m "${PY_GOMODULE}" "$@"
            ;;
    esac
    shift
done

exit 0

