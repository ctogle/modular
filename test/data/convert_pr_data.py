#!/usr/bin/env python
import modular4.output as mo

import argparse,sys,os,time,numpy,logging,multiprocessing,numpy,pdb



def convert(fp,**kws):
    '''
    given a file path and keywords, attempt to parse the contents
      into a list of targets,values,and extra arguments
      produce a modular output object
    '''
    if fp.endswith('.csv'):
        yt,yd,ye = mo.loadcsv(fp,**kws)
        pgs = []
        for yx in range(1,len(yt)):
            ydat = numpy.array((yd[0],yd[yx])).reshape(1,2,yd[0].size)
            pgs.append((ydat,[yt[0],yt[yx]],{'header':str(ye['inducer'][yx])}))
        kws['ol'] = 'none','converteddata','pkl',','.join(yt)
        kws['pages'] = pgs
        kws['inform'] = inform_callback
        kws['MODULARDATA'] = True
        moup = mo.output(**kws)
    else:
        mb.log(5,'unknown data extension',fp[fp.rfind('.'):])
        raise ValueError
    return moup

def inform_callback(e,pg):
    yt,yd,ye = pg

    pdb.set_trace()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--file',required = True,type = str,default = '',help = 'path to input data file')
    options = parser.parse_args()
    if options.file:
        df = os.path.join(os.getcwd(),options.file)
        if not os.path.isfile(df):
            mb.log(5,'COULD NOT LOCATE DATA: %s' % df)
        else:
            moup = convert(df)
            moup()
    else:mb.log(5,'NO FILE PROVIDED')






