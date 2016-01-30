import numpy as np
import random

roll = lambda : random.random() > 0.5

def reflect(p,a,b):
    if p < a:p = a + (a - p)
    if p > b:p = b - (p - b)
    return p
        
def wraparound(p,a,b):
    if p < a:p = b - (a - p)
    if p > b:p = a + (p - b)
    return p

def move(p,d,b,t):
    if d is None:s = random.choice((-1,1))
    else:s = np.sign(d)
    delp = s*random.random()*t*(b[1]-b[0])/3.0
    newp = p + delp
    #newp = reflect(newp,b[0],b[1])
    newp = wraparound(newp,b[0],b[1])
    return newp

def step(x,g,b,t,dg):
    ng = tuple(move(p,d,mm,t) if roll() else p for p,d,mm in zip(g,dg,b))
    return ng

def trimspace(f,x,y,g,b):
    def trim(p,m):
        r = (m[1]-m[0])/3
        m0 = m[0] if p-m[0] < r else p - r
        m1 = m[1] if m[1]-p < r else p + r
        return m0,m1
    newb = tuple(trim(g,m) for g,m in zip(g,b))
    return newb



