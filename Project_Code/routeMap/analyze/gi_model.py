from routeMap.analyze import utilize
import numpy as np

class giModel:
    def __init__(self, lbound:list, ubound:list, side_len:int) -> None:
        a,_,_ = utilize.statistics_from_bbox(lbound, ubound, side_len)
        self.i_max, self.o_max = a.shape
        # variable define
        self.gi = np.zeros(a.shape)
        self.sum_x = int(a.sum())
        self.n = int((a!=0).sum())
        if self.sum_x == 0 or self.n == 1:
            self.gi = self.gi.tolist()
            return
        self.by_v = 1/((self.sum_x**2)*(self.n-1))
        y1 = self.sum_x / self.n
        self.y2 = 0
        for i in range(self.i_max):
            for o in range(self.o_max):
                self.y2 = self.y2 + (a[i][o])**2
        self.y2 = self.y2/self.n- y1**2

        # calculate self.gi
        for i in range(self.i_max):
            for o in range(self.o_max):
                self.gi[i][o] = self.g_star(i,o,1,a)
        self.gi = np.array(self.gi)

        # normalized (max to 0.9)
        self.gi[self.gi == 999] = self.gi.min()
        self.gi[self.gi > 0] = self.gi[self.gi>0]/self.gi.max()
        self.gi[self.gi < 0] = self.gi[self.gi<0]/np.abs(self.gi.min())
        self.gi = np.round(self.gi,5)
        self.gi = self.gi.tolist()
        print("Data ready ~")

    def g_star(self,target_row,target_col,d,data):
        w = 0
        gi = 0
        for i in range(target_row-d,target_row+d+1):
            for o in range(target_col-d,target_col+d+1):
                if i >= 0 and i < self.i_max and o >= 0 and o < self.o_max and data[i][o]!=0:
                    gi = gi + data[i][o]
                    w= w+1
        if w == 0 :
            return 999
        return (gi/self.sum_x - w/self.n)/((w*(self.n-w)*self.y2)*self.by_v)**0.5

    