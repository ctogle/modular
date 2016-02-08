


class mobject(object):

    def _def(self,k,v,**kws):
        if not hasattr(self,k):
            if k in kws:dv = kws[k]
            else:dv = v
            self.__setattr__(k,dv)



