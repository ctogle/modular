import unittest

import modular4.ensemble as me

import pdb,os,sys



class test_mobject(unittest.TestCase):
    pass

class test_ensemble(unittest.TestCase):

    mm_mcfg = os.path.join(os.getcwd(),'MM_kinetics_boring.mcfg')
    cr_mcfg = os.path.join(os.getcwd(),'correl_demo.mcfg')

    def test_parse_run(self):
        r = me.ensemble(name = 'ensem1').parse_mcfg(self.cr_mcfg).run()
        for o in r:o()
        
        pdb.set_trace()

if __name__ == '__main__':
    unittest.main()





