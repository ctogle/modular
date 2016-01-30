import metric
import pspace
import forms

import matplotlib.pyplot as plt
import numpy as np

def heat(i):
    hx = np.linspace(0,i,i)
    hc = forms.exponential(hx,1.0,-3.0)
    return hc

def simanneal(f,x,y,g,b,i,tolerance):
    hc,j = heat(i),0
    m = metric.least_squares(f,x,y,g)  
    ndg = tuple(None for k in g)
    sg = pspace.step(x,g,b,hc[0],ndg)
    while j < i and m.sum() > tolerance:
        t = hc[j]
        j += 1
        sm = metric.least_squares(f,x,y,sg)
        if m.sum() - sm.sum() > 0.0:
            m,g,dg = sm,sg,tuple(g1-g2 for g1,g2 in zip(sg,g))
            sg = pspace.step(x,g,b,t,dg)
        else:sg = pspace.step(x,g,b,t,ndg)
    if j < i:print 'exited early:',j,'/',i
    else:print 'didnt exited early:',j,'/',i
    return g





def simanneal_iter(f,x,y,n,g,m):

    for dn in range(n):
        g = simanneal(f,x,y,g,m)
        if dn < n - 1:
            print 'pretrim',m
            m = pspace.trimspace(f,x,y,g,m)
            print 'posttrim',m

    print 'sim anneal'
    plt.plot(x,y,color = 'black')
    plt.plot(x,f(x,*g),color = 'red')
    plt.show()

    return g






