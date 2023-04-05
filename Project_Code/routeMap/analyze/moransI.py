from routeMap.analyze.gi_model import giModel
import routeMap.analyze.utilize as utilize
import numpy as np
from PIL import Image

class moransModel:
    def __init__(self, lbound:list, ubound:list, side_len:int) -> None:       
        gi = giModel(lbound,ubound,side_len).gi

        self.arr = np.array(gi)
        self.arr = self.arr - self.arr.min()

        self.moransI = np.zeros(self.arr.shape)
        self.avg = np.zeros(self.arr.shape)
        self.cen = 0
        self.row_max, self.col_max = self.arr.shape
        for i in range(self.row_max):
            for o in range(self.col_max):
                self.moransI[i][o] = abs(self.myfun(i,o,6,4))
                if self.arr[i][o] < self.avg[i][o]/169 :
                    self.moransI[i][o] = -self.moransI[i][o]
        self.moransI[self.moransI > 0] = self.moransI[self.moransI>0]/self.moransI.max()
        self.moransI[self.moransI < 0] = self.moransI[self.moransI<0]/-self.moransI.min()
        self.moransI = np.round(self.moransI,3)

    def myfun(self,i,o,d,t):
        sum_x = 0
        n = 0
        n_t = 0
        sum_t = 0
        # avg
        if i>d and i <self.row_max-d-1 and o>d and o<self.col_max-d-1:
            sum_x = self.avg[i][o-1] 
            if i == d+1:
                for ii in range(i-d,i+d+1):
                    sum_x = sum_x - self.arr[ii][o-d-1] + self.arr[ii][o+d]
            else:
                sum_x = sum_x + self.avg[i-1][o] - self.avg[i-1][o-1] \
                    + self.arr[i-d-1][o-d-1] - self.arr[i-d-1][o+d] \
                    - self.arr[i+d][o-d-1] + self.arr[i+d][o+d]
            n = (d*2+1)**2
            sum_t = self.cen
            n_t = (t*2+1)**2
            for ii in range(i-t,i+t+1):
                sum_t = sum_t - self.arr[ii][o-t-1] + self.arr[ii][o+t]
            self.cen = sum_t
        else:
            for ii in range(i-d,i+d+1):
                for oo in range(o-d,o+d+1):
                    if ii >= 0 and ii < self.row_max and oo >= 0 and oo < self.col_max:
                        sum_x = sum_x + self.arr[ii][oo]
                        n = n+ 1
            # center
            for ii in range(i-t,i+t+1):
                for oo in range(o-t,o+t+1):
                    if ii >= 0 and ii < self.row_max and oo >= 0 and oo < self.col_max:
                        sum_t = sum_t + self.arr[ii][oo]
                        n_t = n_t +1
            self.cen = sum_t

        mean_x = sum_x/n
        #print(f'{i},{o} n={n} mean={mean_x} sum_t={sum_t} arr={arr[i][o]}')
        self.avg[i][o] = sum_x
        return self.arr[i][o] * sum_t - n_t * mean_x * self.arr[i][o] - mean_x * sum_t + (mean_x**2)*n_t

    

    def output(self,file = 'test'):
        utilize.array_to_base64_png(self.moransI,alpha=[0.6 if i>0.3 else 0 for i in np.linspace(-1, 1, 256)],saveAs=f"./image/{file}2.png")
        utilize.array_to_base64_png(self.arr,saveAs=f"./image/{file}1.png")
        #background = Image.open(f"./image/{file}2.png")
        #foreground = Image.open(f"./image/{file}1.png")
        #Image.alpha_composite(background, foreground).save(f"./image/{file}3.png")
