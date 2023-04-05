import gzip
import pickle
import math
from pyparsing import conditionAsParseAction
from sklearn.neighbors import KernelDensity
import pymongo
import pickle
import math
from django.http import HttpResponse
import json


fromDatabase = False
# taiwan = []
# city_count = []
# print('loading data...')

if fromDatabase:  # from db
    import pymongo
    myclient = pymongo.MongoClient("mongodb://localhost:27017/")
    mydb = myclient["mydatabase"]
    mycol = mydb["107_TrafficAccident"]  # 107_TrafficAccident
    # for row in mycol.find( {},{"city":1,"lnglat":1,"_id":0}):
    #     #city_count[row['city']] = city_count[row['city']] + 1
    #     taiwan.append(row['lnglat'])
    # taiwan = np.array(taiwan)
else:  # from csv
    import pandas as pd
    from ..analyze import utilize
    # df = pd.read_csv('./Data/107_data.csv')[['lng', 'lat']]
    # a = pd.read_csv('./Data/107_data.csv')[['city','lng','lat']]
    # city_count = pd.read_csv('./Data/analysis.csv',index_col=0).to_numpy().tolist()
    # taiwan = a[['lng','lat']].values


class Taiwan():
    city_list = [
        '臺南市', '臺中市', '雲林縣', '新北市', '高雄市', '宜蘭縣', '花蓮縣', '南投縣', '臺北市', '嘉義市',
        '彰化縣', '臺東縣', '桃園市', '屏東縣', '嘉義縣', '新竹縣', '新竹市', '基隆市', '澎湖縣', '苗栗縣',
        '金門縣', '連江縣'
    ]
    cities_code = {'南投縣': 'M', '嘉義市': 'I', '嘉義縣': 'Q', '基隆市': 'C', '宜蘭縣': 'G', '屏東縣': 'T', '彰化縣': 'N', '新北市': 'F',
                   '新竹市': 'O', '新竹縣': 'J', '桃園市': 'H', '澎湖縣': 'X', '臺中市': 'B', '臺北市': 'A', '臺南市': 'D', '臺東縣': 'V',
                   '花蓮縣': 'U', '苗栗縣': 'K', '連江縣': 'Z', '金門縣': 'W', '雲林縣': 'P', '高雄市': 'E'}


# lboung,ubound for all taiwan city list
b_c_s = [
    [120.02690556700009, 22.887506100000053], [
        120.6562675780001, 23.413741868000045],
    [120.45655266000006, 23.998557382000058], [
        121.45200501700003, 24.44148940900004],
    [119.9968969580001, 23.435707123000043], [
        120.73615724500007, 23.86622234500004],
    [121.28268039500006, 24.67319375900007], [
        122.007494458, 25.300305479000087],
    [114.35928247200002, 10.371347663000051], [
        121.0490304430001, 23.471713519000048],
    [121.31765886400001, 24.309426208000048], [
        124.56114950000006, 25.92913772500009],
    [120.98656461900009, 23.09778067600007], [
        121.77405669200004, 24.37055273900006],
    [120.61549033900008, 23.43541038300009], [
        121.34969556100009, 24.24587331300006],
    [121.45714093900006, 24.960502697000038], [
        121.66593430800003, 25.21017520500004],
    [120.38915221400009, 23.439557556000068], [
        120.509371515, 23.518429800000035],
    [120.2203552200001, 23.78561319000005], [
        120.68394791600008, 24.207186205000085],
    [120.73905203100003, 21.942511678000074], [
        121.61640099600004, 23.443813754000075],
    [120.98202546100003, 24.586456827000063], [
        121.47998818300005, 25.12361560700009],
    [120.35314470500009, 21.756143532000067], [
        120.90418495100005, 22.885178108000048],
    [120.11805319100006, 23.21478445200006], [
        120.95751490300006, 23.63591295300006],
    [120.92522125600004, 24.427375744000138], [
        121.41232290700006, 24.94638910400007],
    [120.87452940000003, 24.71259658700007], [
        121.03353589200006, 24.854813765000138],
    [121.62678621100008, 25.05247269700004], [
        122.10915075700007, 25.63338178500004],
    [119.31429438700002, 23.186564029000067], [
        119.7269789930001, 23.810694694000063],
    [120.62185385400005, 24.28851612400007], [
        121.26263296700006, 24.741091053000048],
    [118.13797245900003, 24.16025806600004], [
        119.47920615500004, 24.999616759000048],
    [119.908897282, 25.940998015000048], [
        120.51174267100009, 26.385278130000074]
]

# compute distance of two point a,b


def longitudeSwap(UR, LL):
    '''
        upper left  <-  upper right

        lower left  ->  lower right
    '''
    return [LL[0], UR[1]], [UR[0], LL[1]]


def calDist(a, b):
    '''
        compute the distance of point (a, b)  
    '''
    return math.hypot(a[0] - b[0], a[1] - b[1])


def calDataSetRange(pointList):
    '''
    compute range of model dataset, return UR2, LL2, UR3, LL3

    UpperRight, LowerLeft
    UR1 ,LL1: range depands on the route {max, min} of {lontitude, latitude}  (trivial => ignore it) 
    UR2, LL2: range depands on the closest city bound
    UR3, LL3: range depands on the ratio square root
    '''
    # ver 1. ideal model depands on the route upper lowwer bound
    maxLng = pointList[0][0]
    minLng = pointList[0][0]
    maxLat = pointList[0][1]
    minLat = pointList[0][1]
    for p in pointList:
        if(p[0] > maxLng):
            maxLng = p[0]
        elif(p[0] <= minLng):
            minLng = p[0]

        if(p[1] > maxLat):
            maxLat = p[1]
        elif(p[1] <= minLat):
            minLat = p[1]

    upperRight = [maxLng, maxLat]    # UR1
    lowwerLeft = [minLng, minLat]    # LL1
    # ver 2. ideal model depands on the closest city bound
    # ////////////////////////////////////////////////
    distUR = 999
    UR2 = upperRight
    distLL = 999
    LL2 = lowwerLeft
    for i in b_c_s:
        # find the closest city lbound
        if (i[0] < LL2[0] and i[1] < LL2[1]) and calDist(i, lowwerLeft) < distLL:
            distLL = calDist(i, lowwerLeft)
            LL2 = i

        # find the closest city ubound
        if (i[0] > UR2[0] and i[1] > UR2[1]) and calDist(i, upperRight) < distUR:
            distUR = calDist(i, upperRight)
            UR2 = i
    # ////////////////////////////////////////////////

    # ver 3. ideal model depands on the ratio square root
    # ////////////////////////////////////////////////
    # 23.077072, 120.042559 大約本島最西
    # 25.013911, 122.029019 大約本島最東
    # ur = 25.014, 122.029
    # ll = 23.077, 120.426
    # 台灣本島估算 經緯度橫跨約2
    taiwanLngCross = 2
    taiwanLatCross = 3
    routeLngCenter = (maxLng+minLng)/2
    routeLatCenter = (maxLat+minLat)/2
    lngCrossLenEnlargement = (math.sqrt((maxLng-minLng)*taiwanLngCross)) / 2
    latCrossLenEnlargement = (math.sqrt((maxLat-minLat)*taiwanLatCross)) / 2
    UR3 = [routeLngCenter + lngCrossLenEnlargement,
           routeLatCenter + latCrossLenEnlargement]
    LL3 = [routeLngCenter - lngCrossLenEnlargement,
           routeLatCenter - latCrossLenEnlargement]

    # ////////////////////////////////////////////////

    return UR2, LL2, UR3, LL3


def tranningModel(ubound, lbound):
    # dataset selection by range

    if fromDatabase:  # from db
        modelPointList = []
        for row in mycol.find({
                '$and': [
                    {
                        'lnglat.0': {
                            '$gt': lbound[0]
                        }
                    }, {
                        'lnglat.1': {
                            '$gt': lbound[1]
                        }
                    }, {
                        'lnglat.0': {
                            '$lt': ubound[0]
                        }
                    }, {
                        'lnglat.1': {
                            '$lt': ubound[1]
                        }
                    }
                ]
        }, {"lnglat": 1, "_id": 0}):
            modelPointList.append(row['lnglat'])
        print('data: ', len(modelPointList))
    else:  # from csv
        modelPointList = utilize.get_data_from_bbox(lbound, ubound)
        print('data: ', len(modelPointList))

    # trainning model
    kdeModel = KernelDensity(
        bandwidth=0.001, kernel="gaussian", atol=1
    ).fit(modelPointList)
    return kdeModel


def kdeCal(pointList, ubound, lbound):
    '''
        compute kde dangerDegree of route 
        model dataset selecton by input range

        preCondition: pointList(route point list), ubound, lbound (upperright, lowerleft)

              pointList format: [ [經度,緯度],[Longitude,Latitude], [120.00,22.000] ... ]
                以api取得之經緯度為先緯度在經度 需先反轉
                ex: for all in pointList: all = all.reverse()

        postCondition: return dangerDegree
    '''
    routeLen = 0
    dangerDeg = 0
    scoreList = []
    partialLenList = []

    # trainning model
    kdeModel = tranningModel(ubound, lbound)

    # compute kde score for all point in pointlist
    scoreList = kdeModel.score_samples(pointList)
    for i in range(0, len(pointList)-1):
        # compute partial distance
        partialLenList.append(calDist(pointList[i], pointList[i+1]))
        routeLen = routeLen + partialLenList[-1]

        # compute avg radius for the point
        avgRadius = 0
        if i == 0:
            partial = partialLenList[-1]/2
        else:
            partial = (partialLenList[-1]+partialLenList[-2])/2

        # add the radius-kde_score index for dangerDegree estimation
        dangerDeg = dangerDeg+partial * math.exp(scoreList[i])

    # add last point
    dangerDeg = (dangerDeg+partialLenList[-1] /
                 2 * math.exp(scoreList[-1]))/routeLen

    return dangerDeg


def kdeCalbyModel(pointList, kdeModel):
    '''
        compute kde dangerDegree of route

        preCondition: pointList(route point list), kde (kde model)

              pointList format: [ [經度,緯度],[Longitude,Latitude], [120.00,22.000] ... ]
                以api取得之經緯度為先緯度在經度 需先反轉
                ex: for all in pointList: all = all.reverse()

        postCondition: return dangerDegree
    '''
    routeLen = 0
    dangerDeg = 0
    scoreList = []
    partialLenList = []

    # compute kde score for all point in pointlist
    scoreList = kdeModel.score_samples(pointList)
    # print(scoreList)

    for i in range(0, len(pointList)-1):
        # compute partial distance
        partialLenList.append(calDist(pointList[i], pointList[i+1]))
        routeLen = routeLen + partialLenList[-1]

        # compute avg radius for the point
        avgRadius = 0
        if i == 0:
            partial = partialLenList[-1]/2
        else:
            partial = (partialLenList[-1]+partialLenList[-2])/2

        # add the radius-kde_score index for dangerDegree estimation
        dangerDeg = dangerDeg+partial * math.exp(scoreList[i])

    # last point
    dangerDeg = (dangerDeg+partialLenList[-1] /
                 2 * math.exp(scoreList[-1]))/routeLen

    return dangerDeg
#example=[[120.21281, 22.99706], [120.21278000000001, 22.9971], [120.21272, 22.99713], [120.21235, 22.9972], [120.21235, 22.997139999999998], [120.21232, 22.997079999999997], [120.21228, 22.997049999999998], [120.21222, 22.997049999999998], [120.21219, 22.996979999999997], [120.21213, 22.996819999999996], [120.21209, 22.996769999999994], [120.21202000000001, 22.996779999999994], [120.21154000000001, 22.996859999999995], [120.21062000000002, 22.996199999999995], [120.20994000000002, 22.995779999999996], [120.20935000000001, 22.995389999999997], [120.20845000000001, 22.994769999999995], [120.20730000000002, 22.994039999999995], [120.20701000000001, 22.993869999999994], [120.20667000000002, 22.993649999999995], [120.20641000000002, 22.993849999999995], [120.20598000000003, 22.994079999999993], [120.20509000000003, 22.994369999999993], [120.20384000000003, 22.994769999999992], [120.20307000000003, 22.995029999999993], [120.20179000000003, 22.995369999999994], [120.20057000000003, 22.995859999999993], [120.19964000000003, 22.996069999999992], [120.19819000000003, 22.996529999999993], [120.19730000000003, 22.996859999999995], [120.19605000000003, 22.997269999999993], [120.19309000000003, 22.998289999999994], [120.19269000000003, 22.998349999999995], [120.19244000000003, 22.998309999999996], [120.19211000000003, 22.998069999999995], [120.19185000000003, 22.997929999999997], [120.19177000000003, 22.997919999999997], [120.19154000000003, 22.99797], [120.19089000000004, 22.99814], [120.18975000000003, 22.998459999999998], [120.18885000000003, 22.9989], [120.18860000000004, 22.99895], [120.18844000000004, 22.99897], [120.18789000000004, 22.99897], [120.18779000000004, 22.999], [120.18766000000004, 22.999039999999997], [120.18742000000003, 22.998969999999996], [120.18713000000002, 22.998899999999995], [120.18697000000003, 22.998869999999997], [120.18665000000003, 22.998889999999996], [120.18598000000003, 22.998959999999997], [120.18480000000002, 22.999089999999995], [120.18425000000002, 22.999089999999995], [120.18334000000002, 22.999109999999995], [120.18239000000001, 22.999089999999995], [120.18122000000001, 22.999049999999997], [120.18014000000001, 22.999039999999997], [120.17893000000001, 22.999079999999996], [120.17760000000001, 22.999119999999994], [120.17661000000001, 22.999179999999996], [120.17628, 22.999169999999996], [120.17506, 22.999229999999997], [120.17478, 22.999269999999996], [120.17359, 22.999659999999995], [120.17251, 23.000029999999995], [120.17138, 23.000449999999994], [120.16893999999999, 23.001279999999994], [120.16842, 23.001469999999994], [120.16793, 23.001669999999994], [120.16771, 23.001759999999994], [120.16758, 23.001789999999993], [120.16722, 23.001849999999994], [120.16694, 23.001929999999994], [120.16572, 23.002349999999993], [120.16498, 23.002629999999993], [120.16482, 23.00266999999999], [120.16461000000001, 23.00268999999999], [120.16439000000001, 23.00267999999999], [120.16425000000001, 23.002639999999992], [120.16414, 23.00258999999999], [120.16397, 23.00243999999999], [120.16379, 23.00249999999999], [120.16337, 23.00261999999999], [120.16273, 23.00274999999999], [120.16212, 23.002879999999987], [120.16102000000001, 23.002869999999987], [120.16112000000001, 23.002659999999988], [120.16118000000002, 23.002379999999988]]
# print(kdeCal(kde_Model,example))
