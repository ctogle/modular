import sim_anneal.anneal as sa
import modular_core.ensemble as mce

import matplotlib.pyplot as plt
import numpy as np
import pdb,os,sys,random,inspect





# plot the best fit, initial fit, and target fit
def plot(f,x,i,a,b):
    ax = plt.gca()
    init = f(x,*i)
    data = f(x,*a)
    best = f(x,*b)
    for j in range(best.shape[0]):
        ax.plot(x,init[j],color = 'b',label = 'initial fit')
        ax.plot(x,data[j],color = 'r',label = 'actual',linestyle = '--')
        ax.plot(x,best[j],color = 'g',label = 'best fit')
    ax.legend()
    plt.show()

# summarize the results of a round of fitting
def summarize(f,x,initial,actual,result,derror):
    error = tuple(abs((r-a)/a) for r,a in zip(result,actual))
    percenterror = np.round(max(error)*100.0,3)
    percentderror = np.round(derror,3)
    print '-'*50
    print 'fit percentage parameter error:',percenterror
    print 'fit percentage data error:',percentderror
    print 'actual:',actual
    print 'result:',result
    print '-'*50
    if 'p' in sys.argv:plot(f,x,initial,actual,result)
    return percenterror

def run_test(f,x,y,a,b,i,**ekwgs):
    if y is None or a is None:
        a = sa.random_position(b)
        y = f(x,*a)
    result,derror = sa.run(f,x,y,b,i,**ekwgs)
    summary = summarize(f,x,i,a,result,derror)
    return result,summary





def new_ensem(mcfg):
    emng = mce.ensemble_manager()
    ensm = emng._add_ensemble('gillespiem')
    ensm.mcfg_path = mcfg
    ensm._parse_mcfg()
    ensm._run_params_to_location_prepoolinit()
    return ensm

def run_ensem(e,**kws):
    psp = e.cartographer_plan.parameter_space
    simu = e.module.simulation
    seed = e.module._set_seed
    espl = e.simulation_plan
    maxtime = espl._max_time()
    captinc = espl._capture_increment()

    def f(x,*p):
        psp._move_to(p)
        e._run_params_to_location()
        rundat = simu(seed(e._seed(),e.module.sim_args))
        return rundat[1:]

    b = tuple(tuple(psp.axes[j].bounds) for j in range(psp.dimensions))
    i = tuple(psp.axes[j]._value() for j in range(psp.dimensions))
    x = np.linspace(0,maxtime,1+maxtime/captinc)

    #a = sa.random_position(b)
    a = (1.0,0.01,800.0)
    y = f(x,*a)

    kws['it'] = 20
    kws['iterations'] = 100000
    kws['heatrate'] = 20.0
    kws['discrete'] = True
    return run_test(f,x,y,a,b,i,**kws)



if __name__ == '__main__':
    mcfg = os.path.join(os.getcwd(),'MM_kinetics_fitting.mcfg')
    r,s = run_ensem(new_ensem(mcfg))
    print 'result,summary',r,s





