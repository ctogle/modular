#!/usr/bin/env bash

PY_GOMODULE="modular4.mrun"
echo "performing mpirun of modular!"
mpiexec --nooversubscribe --hostfile ~/dev/hostfile python -m "${PY_GOMODULE}" "$@"
echo "finished mpirun of modular!"



