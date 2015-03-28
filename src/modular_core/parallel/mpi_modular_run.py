#!/usr/bin/env python

from mpi4py import MPI

import pdb

def test():
    comm = MPI.COMM_WORLD
    print 'hey, im rank %d from %d running in total:' % (comm.rank,comm.size)
    comm.Barrier()
    return comm.rank

test()

def run():
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    #MPI.rank
    #MPI.size

    someinput = ()
    thing = comm.Gather(*someinput)

    if MPI.rank == 0:
        results = []
        for dx in range(len(thing)):
            res = thing[dx]
            results.append(res)

    pdb.set_trace()

#run()



