import modular_core.io.mplt as mplt
import matplotlib.pyplot as plt
import pdb,unittest,numpy,os

#python3 -m unittest discover -v ./ "*tests.py"

class test_mplot(unittest.TestCase):

    def setUp(self):
        #cdir = '/srv/latitude/3-2-df_sync/1000traj_const_prod/'
        cdir1 = '/srv/latitude/3-2-df_sync/1000traj_const_prod/means_output.209.pkl'
        cdir2 = '/srv/latitude/3-2-df_sync/1000traj_const_prod/correlreorg_output.0.pkl'
        cdir3 = '/srv/latitude/3-2-df_sync/1000traj_const_prod/R1statreorg_output.0.pkl'
        cdir4 = '/srv/latitude/3-2-df_sync/1000traj_const_prod/R2statreorg_output.0.pkl'
        cdir5 = '/srv/latitude/3-2-df_sync/1000traj_const_prod/R3statreorg_output.0.pkl'
        self.dffiles = (cdir1,cdir2,cdir3,cdir4,cdir5)

        cdir6 = '/srv/hemlock/correlreorg_output.0.pkl'
        self.dffiles = (cdir6,)

        cdir1 = (os.getcwd(),)
        self.colfiles = (cdir1)

    def __test_linescan(self):

        colormap = plt.get_cmap('jet')
        colors = [colormap(i) for i in numpy.linspace(0,0.9,6)]

        self.mp = mplt.mplot()
        self.mp.open_data(*self.dffiles)

        msub1 = self.mp.subplot('111',xlab = 'alphaR3',ylab = 'correlations',plab = 'Correlations With Different Coupling Strengths',ymin = -0.15,ymax = 0.3)
        msub1.add_line('alphaR3 : value','correlation coefficients',color = colors[0],name = 'eta = 0.0')
        msub1.add_line('alphaR3 : value','correlation coefficients',color = colors[1],name = 'eta = 0.1')
        msub1.add_line('alphaR3 : value','correlation coefficients',color = colors[2],name = 'eta = 0.2')
        msub1.add_line('alphaR3 : value','correlation coefficients',color = colors[3],name = 'eta = 0.3')
        msub1.add_line('alphaR3 : value','correlation coefficients',color = colors[4],name = 'eta = 0.4')
        msub1.add_line('alphaR3 : value','correlation coefficients',color = colors[5],name = 'eta = 0.5')
        msub1.add_line([0,40],[0,0],name = '',color = 'black',style = '--')

        self.mp.render()
        plt.show()

    def test_color(self):
        self.mp = mplt.mplot()
        self.mp.open_data(*self.colfiles)

        msub1 = self.mp.subplot('111',xlab = 'lambda1',ylab = 'correlations',plab = 'correlations: blah blah blah')
        msub1.add_heat('lambda1 : value','lambda2 : value','correlation coefficients')

        self.mp.render()
        plt.show()

    def __test_df_sync_plots(self):
        self.mp = mplt.mplot()
        self.mp.open_data(*self.dffiles)

        msub1 = self.mp.subplot('311',xlab = 'time',ylab = 'mean',plab = 'max correlation: blah blah blah',xmin = 0,xmax = 1000,ymin = 0,ymax = 45)
        msub2 = self.mp.subplot('312',xlab = 'alphaR3',ylab = 'correlation between R1 and R2',legend = False,ymin = -0.05,ymax = 0.3)
        msub3 = self.mp.subplot('325',xlab = 'alhpaR3',ylab = 'final mean value',xmin = 0,xmax = 40,ymin = 0,ymax = 1000,legendloc = 'upper left')
        msub4 = self.mp.subplot('326',xlab = 'alhpaR3',ylab = 'final mean value',xmin = 0,xmax = 10,ymin = 0,ymax = 50,legend = False)

        msub1.add_line('time','R1 mean',name = 'R1',color = 'blue')
        msub1.add_line('time','R2 mean',name = 'R2',color = 'green')
        msub1.add_line('time','R3 mean',name = 'R3',color = 'red')

        msub2.add_line('alphaR3 : value','correlation coefficients',name = '',color = 'blue')
        msub2.add_line([0,40],[0,0],name = '',color = 'black',style = '--')

        msub3.add_line('alphaR3 : value','R1 mean mean',name = 'R1',color = 'blue')
        msub3.add_line('alphaR3 : value','R2 mean mean',name = 'R2',color = 'green')
        msub3.add_line('alphaR3 : value','R3 mean mean',name = 'R3',color = 'red')
        msub3.add_line([0,18],[0,0],name = '',color = 'black',style = '--')
        msub3.add_line([18,40],[0,900],name = '',color = 'black',style = '--')

        msub4.add_line('alphaR3 : value','R1 mean mean',name = 'R1',color = 'blue')
        msub4.add_line('alphaR3 : value','R2 mean mean',name = 'R2',color = 'green')
        msub4.add_line('alphaR3 : value','R3 mean mean',name = 'R3',color = 'red')

        self.mp.render()
        plt.show()

if __name__ == '__main__':
    unittest.main()










