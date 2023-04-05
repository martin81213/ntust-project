from sklearn.neighbors import KernelDensity
from . import utilize
import numpy as np

def calculate_high(lbound,ubound):
    #import time
    #old = time.time()
    # query

    a = utilize.get_data_from_bbox(lbound,ubound)

    # img size
    side_len = (ubound[0]-lbound[0])/50
    bandwidth =(ubound[0]-lbound[0])*0.008
    row,col =  ( int((ubound[1]-lbound[1])/side_len)+1,int((ubound[0]-lbound[0])/side_len)+1)

    if len(a) != 0:
        # model 
        #old = time.time()
        kde = KernelDensity(
            kernel="gaussian",
            atol=1
            ).fit(a)
        kde.set_params(bandwidth = bandwidth)

        # position in map
        pos = []
        for i in range(row):
            for o in range(col):
                pos.append([o*side_len+lbound[0],i*side_len+lbound[1]])
        score = kde.score_samples(pos).reshape((row,col))
        #print(time.time() - old)
        # 0.1-0.02
        score[score < 0] = 0

    else:
        score = np.zeros((row,col))
    
    return utilize.array_to_base64_png(score)


def calculate_low(lbound,ubound):
    # kde
    taiwan_kde = KernelDensity(
            kernel="gaussian",
            atol=1
            ).fit(utilize.taiwan)
    side_len = (ubound[0]-lbound[0])/30
    row,col =  ( int((ubound[1]-lbound[1])/side_len)+1,int((ubound[0]-lbound[0])/side_len)+1)
    # model  
    taiwan_kde.set_params(bandwidth = side_len*0.3)
    pos = []
    for i in range(row):
        for o in range(col):
            pos.append([o*side_len+lbound[0],i*side_len+lbound[1]])
    score = taiwan_kde.score_samples(pos).reshape((row,col))
    score[score < 0] = 0

    return utilize.array_to_base64_png(score)