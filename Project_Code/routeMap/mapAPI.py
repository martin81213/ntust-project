import json
from django.http import HttpResponse
import re
import numpy as np
import os.path
from django.views.decorators.clickjacking import xframe_options_exempt
from bson import decode
import requests
import flexpolyline as fp
from routeMap.analyze import utilize
from routeMap.analyze import kde
from routeMap.route import kdemodel
from routeMap import route

def box(request):
    '''
        POST kde image   \n
        Method: GET \n
        Parameter: bbox[lat, lng] \n
        Response: \n
        {
            "img": png,
            "lbound": lbound[lng, lat],
            "ubound": ubound[lng, lat],
        }
    '''

    if request.method == "POST":
        if 'bbox' not in request.POST:
            return HttpResponse(status=400)
        # get bbox
        para = request.POST['bbox']
        if type(para) != str:
            return HttpResponse(status=400)
        bbox = np.array(re.findall(
            r"[-+]?(?:\d*\.\d+|\d+)", para)).astype(float)
        if len(bbox) != 4:
            return HttpResponse(status=400)
        lbound = [bbox[1], bbox[0]]
        ubound = [bbox[3], bbox[2]]

        try:
            # return
            d = {
                "img": "data:image/png;base64," + kde.calculate_high(lbound, ubound),
                "lbound": lbound,
                "ubound": ubound,
            }
        except Exception as e:
            print(e)
            kde.utilize.plt.close()
            return HttpResponse(status=500)

        resp = HttpResponse([json.dumps(d)])
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp




def getImg(request):
    '''
        Get mor image from Project_code/image   \n
        Method: GET \n
        Parameter: id, filename e.g. 0_0_1, 5_5_2 \n
        Response: \n
        {
            "img": png,
            "lbound": lbound[lng, lat],
            "ubound": ubound[lng, lat],
        }
    '''
    

    if request.method == "GET":
        # get para
        if 'id' not in request.GET:
            return HttpResponse('para error', status=400)
        id = request.GET['id']
        if type(id) != str:
            return HttpResponse(status=400)

        # check path safe
        base_dir = './image/'
        dir_path = os.path.realpath(base_dir)
        requested_path = base_dir + id + '.png'
        if os.path.commonprefix((os.path.realpath(requested_path), dir_path)) != dir_path or not os.path.exists(requested_path):
            return HttpResponse('path error', status=404)

        # extract row, col
        a = id.split('_')
        r, c = 0, 0
        try:
            r = int(a[0])
            c = int(a[1])
        except:
            return HttpResponse('para format error', status=400)

        lbound = np.array([120.01930, 21.86400]) + [0.1802 * r, 0.1802 * c]
        ubound = lbound + [0.1802, 0.1802]

        # return
        d = {
            "img": "data:image/png;base64," + utilize.base64.b64encode(open(requested_path, 'rb').read()).decode("utf-8"),
            "lbound": lbound.tolist(),
            "ubound": ubound.tolist()
        }
        # respond
        resp = HttpResponse(json.dumps(d))
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp


def curve(request):
    '''
        Calculate road curve   \n
        Method: POST \n
        Parameter: polyline, use google polyline encode \n
        Response: list of [count, dangerous]\n
        Example:
        >>> encode_example = 'sfbwCwaxcVDAF?JB`DtAfAf@f@RRLPFTLRFXHH@fAPLDRDD@lA`@d@JbATTFf@HfEf@rANd@BdC?X@hBB\\?NANCHC^Ox@[FEBEFIBGDQFu@'
        >>> dangerous_list_example = [0, 1, 1, 0, 2, 2, 1, 0]
        # output
        [[1, 0], [2, 1], [1, 0], [2, 2], [1, 1], [1, 0]]
    '''
    if request.method == "POST":
        from routeMap import route
        if 'polyline' not in request.POST:
            return HttpResponse(status=400)
        poly = request.POST['polyline'].split(',')

        if len(poly) < 1:
            return HttpResponse(status=400)

        returnData = []
        for p in poly:
            try:
                point_list = route.polyline.decode(p)
            except route.polyline.decodeError as e:
                return HttpResponse(status=400)
            returnData.append(route.curvature.road_dangerous(point_list))

        # respond
        resp = HttpResponse(json.dumps(returnData))
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp


def cal_dangerous(request):
    '''
        Calculate road kde dangerous Degree   \n
        Method: POST \n
        Parameter: route polyline, use google polyline encode \n
        Response: 
            dangerDeg: list[float]
        Example:
        >>> encode_example = 'sfbwCwaxcVDAF?JB`DtAfAf@f@RRLPFTLRFXHH@fAPLDRDD@lA`@d@JbATTFf@HfEf@rANd@BdC?X@hBB\\?NANCHC^Ox@[FEBEFIBGDQFu@'
        >>> dangerous_list_example = [0, 1, 1, 0, 2, 2, 1, 0], route in order color: blue, yellow, pink, light blue
        # output 
        [[1, 0], [2, 1], [1, 0], [2, 2], [1, 1], [1, 0]]
    '''
    if request.method == "POST":

        
        polys = request.POST['polyline']
        polys = json.loads(polys)

        # decode route polyline and inverse point list
        routeList = []
        for poly in polys:
            routeList.append(route.polyline.decode(poly))
            for all in routeList[-1]:
                all = all.reverse()

        # dataset selection, trainning model, compute danger degree
        routesDangerDeg = []
        UR2, LL2, UR3, LL3 = kdemodel.calDataSetRange(routeList[0])
        model = kdemodel.tranningModel(UR3, LL3)
        for r in routeList:
            # import gzip
            # import pickle
            # with gzip.open('./routeMap/route/kdeModel.pickle', 'rb') as f:
            # kde_Model = pickle.load(f)
            routesDangerDeg.append(kdemodel.kdeCalbyModel(r, model))

        # return routesDangerDeg(in order), dataset range(bound1: method2, bound2: method3)
        ubound1, lbound1 = kdemodel.longitudeSwap(UR2, LL2)
        ubound2, lbound2 = kdemodel.longitudeSwap(UR3, LL3)
        outcome = {
            "dangerDeg": routesDangerDeg,
            "lbound1": lbound1,  # blue
            "ubound1": ubound1,
            "lbound2": lbound2,  # red
            "ubound2": ubound2
        }
        resp = HttpResponse([json.dumps(outcome)])
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp



def road_block(request):
    '''
        url = requests.get("https://router.hereapi.com/v8/routes?apikey=de8KqchS3znBhAhEXFhpPGsQBCquCv-m5IZyZRLTaH0&origin=52.514717,13.381876&destination=52.536571,13.406953&return=polyline,summary,actions,instructions&transportMode=car&avoid[areas]=bbox:13.38549,52.52836,13.375606,52.523514|bbox:13.407838,52.528001,13.398397,52.524411|bbox:13.39943,52.522661,13.389989,52.519565")
        text = url.text
        data = json.loads(text)
        路障function
        origin = '52.514717,13.381876'
        destination = '52.536571,13.406953'
        avoid[areas] = 'bbox:13.38549,52.52836,13.375606,52.523514|bbox:13.407838,52.528001,13.398397,52.524411'
        example: /road_block?origin=25.0419186%2C121.5645202&destination=25.0942383%2C121.5875907&block=bbox%3A121.56564759705701%2C25.044011071197684%2C121.56683313344159%2C25.042757166481177&alternatives=3
        respond:
            "dangerDeg",
            'curve',
            'pointList'
    '''
    if request.method == "POST":
        origin = request.POST['origin']
        destination = request.POST['destination']
        block = request.POST['block']
        alternative_number = request.POST['alternatives']
        data = {'apikey': 'de8KqchS3znBhAhEXFhpPGsQBCquCv-m5IZyZRLTaH0', 'origin': origin, 'destination': destination, 'return': 'polyline',
                'transportMode': 'car', 'avoid[areas]': block, 'alternatives': alternative_number}
        r = requests.get('https://router.hereapi.com/v8/routes', params=data)
        output = json.loads(r.text)

        
        decode_route = []
        curveList = []
        for i in range(0, len(output['routes'])):
            # point list
            _route = fp.decode(output['routes'][i]['sections'][0]['polyline'])
            # calculate curve dangerous
            curveList.append(route.curvature.road_dangerous(_route))
            decode_route.append(_route)

        # kde route ...
        routeList = []
        for poly in decode_route:
            _route = []
            for point in poly:
                _route.append([point[1],point[0]])
            routeList.append(_route)
        # dataset selection, trainning model, compute danger degree
        routesDangerDeg = []
        _, _, UR3, LL3 = kdemodel.calDataSetRange(routeList[0])
        model = kdemodel.tranningModel(UR3, LL3)
        for r in routeList:
            routesDangerDeg.append(kdemodel.kdeCalbyModel(r, model))


        resp = HttpResponse(json.dumps({
            "dangerDeg": routesDangerDeg,
            'curve':curveList,
            'pointList':decode_route
        }))
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
