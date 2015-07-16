import modular_core.fundamental as lfu
lfu.using_gui = True

from modular_core.ensemble import ensemble_manager
import modular_core.io.mpkl as lpkl
import modular_core.data.single_target as mds

import cStringIO as csio
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

def valid(x):
    return not (math.isnan(x) or math.isinf(x))

def fetch_data_targets(which):
    meanfile = os.path.join(os.getcwd(),'other_data',which+'_dizzy.csv')
    with open(meanfile) as f:
        csvdat = csv.reader(f)
        dheaders = [x for x in csvdat.__iter__()][0][1:]
        dheaders = [x.strip() for x in dheaders]
    return dheaders

def grab_mdata(which):
    pklpath = which+'.0.pkl'
    dcont = lpkl.load_pkl_object(pklpath)
    relevt = lambda x:'mean' in x or '1 stddev of' in x or 'time' in x
    drelev = [relevt(d.name) for d in dcont.data]
    mdaters = [dcont.data[x] for x in range(len(dcont.data)) if drelev[x]]
    return mdaters

def grab_ddata(which,tdx):
    ddaters = []
    meanfile = os.path.join(os.getcwd(),'other_data',which+'_dizzy.csv')
    with open(meanfile,'rb') as f:
        csviter = [x.strip() for x in f.readlines()]
        csviter = [x.split(',') for x in csviter if not x == '']
        csvdat = csv.reader(f)
        #csvdaters = zip(*csvdat.__iter__())
        csvdaters = zip(*csviter)

        try:csvtdat = csvdaters[0]
        except:pdb.set_trace()

        csvmdat = csvdaters[tdx]
        mdater = mds.scalars(name = csvmdat[0],
            data = numpy.array(csvmdat[1:],dtype = numpy.float))
        meantime = mds.scalars(name = csvtdat[0],
            data = numpy.array(csvtdat[1:],dtype = numpy.float))
        ddaters.append(meantime)
        ddaters.append(mdater)
    '''#
    stdfile = os.path.join(os.getcwd(),'other_data',which+'_dizzy.csv')
    with open(stdfile) as f:
        csvdat = csv.reader(f)
        csvdat = [x[tdx] for x in csvdat]
        sdater = mds.scalars(name = csvdat[0],
            data = numpy.array(csvdat[1:],dtype = numpy.float))
        ddaters.append(sdater)
    '''#
    return ddaters

def compare_dater_metrics(report,which,mdata,ddata,sqrtn,plot = True):
    mdiffs = [x-y for x,y in zip(mdata[1].data,ddata[1].data)]
    sdiffs = [x-y for x,y in zip(mdata[2].data,ddata[2].data)]

    zmetric = [sqrtn*(x/y) for x,y in zip(mdiffs,ddata[2].data)]
    zmetric = [abs(z) for z in zmetric if valid(z)]
    zmetric_max = max(zmetric) if zmetric else 0.0

    ymconst = sqrtn/(2.0**0.5)
    ymetric = [ymconst*(((x/y)**2)-1) for x,y 
        in zip(mdata[2].data,ddata[2].data)]
    ymetric = [abs(y) for y in ymetric if valid(y)]
    ymetric_max = max(ymetric) if ymetric else 0.0

    passed = 'passed' if zmetric_max < 3.0 and ymetric_max < 5.0 else 'failed'
    report.write('\n\n\t'+passed+' test '+which)
    report.write('\n\t\twith z-mean-metric value:\t'+str(zmetric_max))
    report.write('\n\t\tand y-stddev-metric value:\t'+str(ymetric_max))

    if plot and passed == 'failed':
        plottable = [
            (mdata[0].data,mdata[1].data,'gillespiem-mean'),
            (mdata[0].data,mdata[2].data,'gillespiem-stddev'),
            (ddata[0].data,ddata[1].data,'dsmts-mean'),
            (ddata[0].data,ddata[2].data,'dsmts-stddev'),
            (ddata[0].data,mdiffs,'differences of means'),
            (ddata[0].data,sdiffs,'differences of stddevs'),
            (ddata[0].data,zmetric,'z-metric of means'),
            (ddata[0].data,ymetric,'y-metric of stddevs'),
                ]
        plot_data(plottable)
        plt.show()

    return passed == 'passed'

def compare_dater_percents(report,which,mdata,ddata,sqrtn,plot = True):
    mperc = [x/y if y > 0.0 else x/(y+0.000001) 
        for x,y in zip(mdata[1].data,ddata[1].data)]
    #sperc = [x/y for x,y in zip(mdata[2].data,ddata[2].data)]

    if len([x for x in mperc if valid(x)]) < len(ddata[0].data):pdb.set_trace()

    mperc = [abs(1-x) for x in mperc if valid(x)]
    #sperc = [abs(1-x) for x in sperc if valid(x)]

    mpercerror = max(mperc) if mperc else 0.0
    #spercerror = max(sperc) if sperc else 0.0

    #passed = 'passed' if mpercerror < 0.02 and spercerror < 0.02 else 'failed'
    passed = 'passed' if mpercerror < 0.02 else 'failed'
    report.write('\n\n\t'+passed+' test '+which)
    report.write('\n\t\twith mean-percent-error:\t'+str(100*mpercerror))
    #report.write('\n\t\tand stddev-percent-error:\t'+str(100*spercerror))

    #if plot and passed == 'failed':
    if plot:
        plottable = [
            (mdata[0].data,mdata[1].data,'gillespiem-mean'),
            #(mdata[0].data,mdata[2].data,'gillespiem-stddev'),
            (ddata[0].data,ddata[1].data,'dizzy-mean'),
            #(ddata[0].data,ddata[2].data,'dsmts-stddev'),
            (ddata[0].data,mperc,'error percentage of means'),
            #(ddata[0].data,sperc,'error percentage of stddevs'),
                ]
        plot_data(plottable)
        plt.show()

    return passed == 'passed'

def compare_data(report,which,sqrtn,plot = True):
    dtargets = fetch_data_targets(which)
    passed = True
    for dtdx in range(len(dtargets)):
        dtarget = which+'-'+dtargets[dtdx]
        ddata = grab_ddata(which,dtdx+1)
        mdata = grab_mdata(dtarget)
        ptest = compare_dater_percents(report,dtarget,ddata,mdata,sqrtn,plot)
        #mtest = compare_dater_metrics(report,dtarget,ddata,mdata,sqrtn,plot)
        #if not ptest and not mtest:return False
        #if not ptest:return False
        if not ptest:passed = False
    return passed

def run_test(report,ensem,mcfgfile,n,plots):
    report.write('\n\tperformed test for mcfg:\t'+mcfgfile)

    mcfg = os.path.join(os.getcwd(),'other_mcfgs',mcfgfile)
    ensem._run_mcfg(mcfg,n)
    ensem._output()

    sqrtn = math.sqrt(ensem.num_trajectories)
    passed = compare_data(report,mcfgfile.replace('.mcfg',''),sqrtn,plots)
    report.write('\n\n'+'#'*80+'\n\n')
    return passed

def run_tests(n = 10000,plots = False):
    report = csio.StringIO()
    mfiles = sorted(os.listdir(os.path.join(os.getcwd(),'other_mcfgs')))
    mnger = ensemble_manager()
    ensem = mnger._add_ensemble(module = 'gillespiem')

    report.write('\n'+'#'*80+'\n\tran other tests for gillespiem\n'+'#'*80+'\n')
    report.write('\n\t found the following mcfgs for testing:\n')
    for mf in mfiles:report.write('\n\t\t'+mf)
    report.write('\n\n'+'#'*80+'\n')

    results = []
    for mf in mfiles:results.append(run_test(report,ensem,mf,n,plots))

    report.write('\n'+'#'*80+'\n\tfinished other tests for gillespiem')
    report.write('\npassed '+str(results.count(True)))
    report.write(' / '+str(len(results))+' tests')
    report.write('\n'+'#'*80+'\n')
    print '\n\treporting...\n'+'#'*80+'\n',report.getvalue()

if __name__ == '__main__':
    run_tests(100000,True)





