import modular_core.fundamental as lfu
lfu.using_gui = True

from modular_core.ensemble import ensemble_manager
import modular_core.io.mpkl as lpkl
import modular_core.data.single_target as mds

import matplotlib.pyplot as plt
import pdb,os,csv,math,numpy

def plot_data(data):
    ax = plt.gca()
    ax.cla()
    ax.grid(True)
    for d in data:ax.plot(d[0],d[1],label = d[2])
    leg = ax.legend()
    leg.draggable()
    plt.show()

def grab_data(which):
    pklpath = which+'.0.pkl'
    dcont = lpkl.load_pkl_object(pklpath)
    relevt = lambda x:'mean' in x or '1 stddev of' in x or 'time' in x
    drelev = [relevt(d.name) for d in dcont.data]
    mdaters = [dcont.data[x] for x in range(len(dcont.data)) if drelev[x]]
    ddaters = []
    meanfile = os.path.join(os.getcwd(),'DSMTS_data',which+'-mean.csv')
    with open(meanfile) as f:
        csvdat = csv.reader(f)
        csvtdat,csvmdat = zip(*csvdat.__iter__())
        mdater = mds.scalars(name = csvmdat[0],
            data = numpy.array(csvmdat[1:],dtype = numpy.float))
        meantime = mds.scalars(name = csvtdat[0],
            data = numpy.array(csvtdat[1:],dtype = numpy.float))
        ddaters.append(meantime)
        ddaters.append(mdater)
    stdfile = os.path.join(os.getcwd(),'DSMTS_data',which+'-sd.csv')
    with open(stdfile) as f:
        csvdat = csv.reader(f)
        csvdat = [x[1] for x in csvdat]
        sdater = mds.scalars(name = csvdat[0],
            data = numpy.array(csvdat[1:],dtype = numpy.float))
        ddaters.append(sdater)
    return mdaters,ddaters

def compare_data(which,sqrtn,stops = True,plot = True):
    mdata,ddata = grab_data(which)
    mdiffs = [x-y for x,y in zip(mdata[1].data,ddata[1].data)]
    sdiffs = [x-y for x,y in zip(mdata[2].data,ddata[2].data)]
    zmeans = [sqrtn*(x/y) for x,y in zip(mdiffs,ddata[2].data)]
    zmetric_max = max([abs(z) for z in zmeans 
        if not math.isnan(z) and not math.isinf(z)])

    #s_t_2 = (1.0/sqrtn**2)

    passed = zmetric_max < 3.0
    print 'passed',passed,'test',which,'with z-mean-metric value',zmetric_max
    if stops:raw_input('\n\tpress any key to continue...\n')
    if plot:
        plottable = [
            (mdata[0].data,mdata[1].data,'gillespiem-mean'),
            (mdata[0].data,mdata[2].data,'gillespiem-stddev'),
            (ddata[0].data,ddata[1].data,'dsmts-mean'),
            (ddata[0].data,ddata[2].data,'dsmts-stddev'),
            (ddata[0].data,mdiffs,'differences of means'),
            (ddata[0].data,sdiffs,'differences of stddevs'),
            (ddata[0].data,zmeans,'z-metric of means'),
                ]
        plot_data(plottable)
        plt.show()
    return passed

def run_test(ensem,mcfgfile,stops):
    print 'performing test for mcfg:'+mcfgfile
    mcfg = os.path.join(os.getcwd(),'DSMTS_mcfgs',mcfgfile)
    ensem._run_mcfg(mcfg)
    ensem._output()
    ensem.module._writer._uninstall()
    sqrtn = math.sqrt(ensem.num_trajectories)
    passed = compare_data(mcfgfile.replace('.mcfg',''),sqrtn,stops)
    return passed

def run_tests(stops = True):
    mnger = ensemble_manager()
    ensem = mnger._add_ensemble(module = 'gillespiem')
    print '\n'+'#'*80+'\n\trunning dsmts tests for gillespiem\n'+'#'*80+'\n'
    mfiles = sorted(os.listdir(os.path.join(os.getcwd(),'DSMTS_mcfgs')))
    print '\t found the following mcfgs for testing:'
    for mf in mfiles:print mf
    if stops:raw_input('\n\tpress any key to continue...\n')
    print '\n'+'#'*80+'\n'
    results = []
    for mf in mfiles:results.append(run_test(ensem,mf,stops))
    print '\n'+'#'*80+'\n\tfinished dsmts tests for gillespiem'
    print 'passed',results.count(True),'/',len(results),'tests'
    print '#'*80+'\n'

if __name__ == '__main__':
    run_tests()





