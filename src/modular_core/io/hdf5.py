import h5py

import pdb,os,numpy





def test():
    hfi = os.path.join(os.getcwd(),'h5test.hdf5')
    hfh = h5py.File(hfi,'w',libver = 'latest')
    
    dname = 'h5testdata';dshape = (5,50);dtype = numpy.float
    data = numpy.ones(dshape,dtype = dtype)
    dset = hfh.create_dataset(dname,data = data)

    pdb.set_trace()

    hfh.close()

test()





