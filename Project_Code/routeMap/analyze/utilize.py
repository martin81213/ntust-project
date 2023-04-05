import os
# shape() is a function to convert geo objects through the interface
import numpy as np
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from matplotlib.colors import ListedColormap
import math

city_list =[
      '臺南市','臺中市','雲林縣','新北市','高雄市','宜蘭縣','花蓮縣','南投縣','臺北市','嘉義市',
      '彰化縣','臺東縣','桃園市','屏東縣','嘉義縣','新竹縣','新竹市','基隆市','澎湖縣','苗栗縣',
      '金門縣','連江縣'
   ]

cities_code = {'南投縣': 'M', '嘉義市': 'I', '嘉義縣': 'Q', '基隆市': 'C', '宜蘭縣': 'G', '屏東縣': 'T', '彰化縣': 'N', '新北市': 'F',
            '新竹市': 'O', '新竹縣': 'J', '桃園市': 'H', '澎湖縣': 'X', '臺中市': 'B', '臺北市': 'A', '臺南市': 'D', '臺東縣': 'V',
            '花蓮縣': 'U', '苗栗縣': 'K', '連江縣': 'Z', '金門縣': 'W', '雲林縣': 'P', '高雄市': 'E'}


fromDatabase = False

taiwan = []
city_count = []
print('loading data...')

if fromDatabase: # from db
    import pymongo
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["mydatabase"]
    mycol = mydb["107_TrafficAccident"] # 107_TrafficAccident
    for row in mycol.find( {},{"city":1,"lnglat":1,"_id":0}):
        #city_count[row['city']] = city_count[row['city']] + 1
        taiwan.append(row['lnglat'])
    taiwan = np.array(taiwan)
else: # from csv
    import pandas as pd
    a = pd.read_csv('./Data/107_data.csv')[['city','lng','lat']]
    city_count = pd.read_csv('./Data/analysis.csv',index_col=0).to_numpy().tolist()
    taiwan = a[['lng','lat']].values

print('data: ',len(taiwan))

def get_data_from_bbox(lbound:list,ubound:list)->list:
    '''
    Get all accident position within boundary box.
    ### Parameter : 
        `lbound`, `ubound`: list[lng,lat] 
        
    ### Return :  
        list of [lng,lat]

    ## Example :
        >>> lb = [120, 23]
        >>> ub = [123, 24]
        >>> utilize.get_data_from_bbox(lb, ub)
        array([[120.578892,  23.962235],
                ...,
                [120.69738 ,  23.978888]])
        
    '''
    return taiwan[
        np.logical_and(
            np.logical_and(taiwan[:,0] > lbound[0],taiwan[:,1] > lbound[1]),
            np.logical_and(taiwan[:,0] < ubound[0],taiwan[:,1] < ubound[1])
        )
    ]

def boundary_city(target_city:list[str]):
    '''
    Get city boundary from shape file
    ### Parameter :
        `target_city`: list[str]
            e.g.['臺北市','桃園市']

    ### Return :
        boundary box: (lb, ub)
    
    ### Example :
        >>> utilize.boundary_city(['臺北市'])
        ([121.45714093900006, 24.960502697000038],
        [121.66593430800003, 25.21017520500004])
    '''
    target_city = [{"city": i} for i in target_city]
    return boundary(target_city)


def boundary(target):
    '''
    Get city boundary from shape file
    ### Parameter :
        `target`: query
            e.g. [{'city':'臺北市'},{{'city':'桃園市'}}]

    ### Return :
        boundary box
    '''
    import shapefile
    shp_path = './Data/city_map.zip'
    assert os.path.exists(shp_path), "Input file does not exist."
    shp = shapefile.Reader('./Data/city_map.zip')

    all_shapes = np.array(shp.shapeRecords())
    records = np.array(shp.records())
    lbound = [360,360]
    ubound = [0,0]
    for city in target:
        bound = all_shapes[np.where(records[:, 0] == cities_code[city['city']])[0][0]].shape.bbox
        lbound = [min(lbound[0],bound[0]),min(lbound[1],bound[1])]
        ubound = [max(ubound[0],bound[2]),max(ubound[1],bound[3])]
        
    return lbound, ubound


def statistics_city(city, side_len):
    '''
    Statistics city accident use side len
    ### Parameter :
        `city`: list   e.g.['臺北市','桃園市']
        `side_len`: int, in meter

    ### Return
        (2D array, lb, ub)

    ### Example :
        >>> utilize.statistics_city(['臺北市'],500)
        (array([[0., ...., 0.],
                     ....
                [0., ...., 0.]]),
        [121.45714093900006, 24.960502697000038],
        [121.66593430800003, 25.21017520500004])
    '''
    lbound, ubound = boundary_city(city)
    return statistics_from_bbox(lbound,ubound,side_len)


def statistics_from_bbox(lbound:list, ubound:list, side_len:int):
    '''
    Statistics bbox accident use side len
    ### Parameter :
        `lbound`: list[lng,lat]
        `ubound`: list[lng,lat]
        `side_len`: int
        
    ### Return
        (2D array, lb, ub)
    
    '''
    side_len = side_len * 0.00000901
    by_len = 1/side_len
    
    a = np.zeros((math.ceil((ubound[1]-lbound[1])*by_len),
                 math.ceil((ubound[0]-lbound[0])*by_len)))
    print("Size: ", a.shape)
    data = get_data_from_bbox(lbound,ubound)
    for row in data:
        i = int((row[1] - lbound[1])*by_len)
        o = int((row[0] - lbound[0])*by_len)
        try:
            a[i][o] = a[i][o]+1
        except:
            # print(i,o)
            pass
    return a, lbound, ubound


def array_to_base64_png(arr:list, mode="heatmap", alpha:list=[], saveAs="", show=False):
    '''
    Array to base64 png format
    ### Parameter :
        `arr`: 2d arraylike, bottom left(0, 0) \n
        `mode`: 'heatmap' | 'Grey'  default:'heatmap' \n
        `alpha`: list\n
            defalut: [min(0.5+i*0.5, 0.5) for i in np.linspace(-1, 1, cmap.N)]  \n
            description: \n
                score 0% - 50% -> 0 - 0.5 \n 
                score 50% up -> 0.5       \n
                cmap.N = 256
        `saveAs`: str, filename
        `show`: bool, whether show inline or not, default: false

    ### Reutrn
        str

    ### Example :
        >>> array = [[1,2],
        >>>         [1,0]]
        >>> utilize.array_to_base64_png(array,show=True)
        'iVBORw0KGgoAA...'
    '''
    cmap = plt.cm.jet
    if mode == "Grey":
        cmap = plt.cm.Greys
    # Get the colormap colors
    my_cmap = cmap(np.arange(cmap.N))
    # Set alpha
    if alpha == []:
        my_cmap[:, -1] = [min(0.5+i*0.5, 0.5) for i in np.linspace(-1, 1, cmap.N)]
    else:
        my_cmap[:, -1] = alpha

    # Create new colormap
    my_cmap = ListedColormap(my_cmap)
    # draw
    plt.imshow(arr, interpolation="bilinear",
               cmap=my_cmap, aspect='equal', origin="lower")
    plt.axis("off")
    
    # to base64
    my_stringIObytes = io.BytesIO()
    plt.savefig(my_stringIObytes, format='png',transparent=True,bbox_inches='tight',pad_inches=0)
    if saveAs != "":
        plt.savefig(saveAs, format='png',transparent=True,bbox_inches='tight',pad_inches=0)

    if show:
        plt.show()
        
    plt.clf()
    plt.close()
    my_stringIObytes.seek(0)
    my_base64_Data = base64.b64encode(my_stringIObytes.read())
    return my_base64_Data.decode("utf-8")


def array_output(arr, min_, max_, bins, ylim=None, show=True, saveAs=""):
    '''
    Array to histogram
    ### Parameter:
        `arr`: arraylike
        `min_`: number, X axis minimum
        `max_`: number, X axis maximum
        `bins`: int, how many bins
        `ylim`: number, Y axis maximun
        `show`: bool, show inline and each value of bin
        `saveAs`: str, filename
    ### Return
        no return value
    
    '''
    if not type(np.array([])).__module__ == np.__name__:
        arr = np.array(arr)
    step = (max_ - min_)/bins
    X = [min_ + step * i for i in range(bins)]
    Y = []
    for x in X:
        x1 = x + step
        Y.append(np.count_nonzero(np.logical_and(arr >= x, arr < x1)))
    if not ylim == None:
        plt.ylim(0, ylim)

    plt.bar(X, Y, width=step*0.7)
    if not saveAs == "":
        plt.title(saveAs)
        plt.savefig(saveAs)
    if show:
        print('sort', sorted(Y, reverse=True))
        print(Y)
        plt.show()
    plt.close()
