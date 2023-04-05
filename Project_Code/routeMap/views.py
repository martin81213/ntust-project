import json
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import pointBox
import datetime as dt
from dateutil import relativedelta
import math

# web page
def home(request):
    '''
        render test.html 
    '''
    return redirect('map/')


def map_page(request):
    id = ''
    if 'id' in request.GET:
        id = request.GET['id']
    return render(request, 'map.html',{'img':id})


# api
def insertPoint(request):               #新增特殊事件點
    try:
        if request.method == "POST":
            posterName_ = request.POST['posterName']
            situaName_ = request.POST['situaName']
            coordinate_ = f"{request.POST['lng']}&{request.POST['lat']}"
            situation_ =  str(request.POST['situation'])
            remark_ = request.POST['remark']
            picLink_ = ''
            if 'picLink' in request.FILES:
                picLink_ = request.FILES['picLink']
            physicalAddr_ = request.POST['physicalAddr']
            #Date process
            startDate_ = str(dt.datetime.now())
            next_Xmonth = dt.datetime.today() + relativedelta.relativedelta(months=3)
            endDate_ = str(next_Xmonth)

            unit = pointBox.objects.create(posterName=posterName_, situaName=situaName_, coordinate=coordinate_,
                                           situation=situation_, remark=remark_, picLink=picLink_, 
                                           startDate=startDate_, endDate=endDate_, physicalAddr=physicalAddr_)
            unit.save()
            return HttpResponse("Successed", status=200)
        return HttpResponse("", status=405)
    except Exception as e:
        print(e, "insertPoint 函式發生問題")
        return HttpResponse('server內部發生錯誤: insertPoint()', status=400)


def modifyPopularNum(request):            #調整特殊點的推廣值（值越大代表越重要)每呼叫一次分數加一
    try:
        if request.method == "POST":
            id_ = request.POST['id']
            unit = pointBox.objects.get(id=int(id_))
            unit.popularNum += 1
            unit.save()
            return HttpResponse("Successed", status=200)
        return HttpResponse("", status=405)
    except Exception as e:
        print(e, "incPopularNum 函式發生問題")
        return HttpResponse('server內部發生錯誤: incPopularNum()', status=400)

def solvePoint(request):                    #把特殊點改為已解決 之後就不用呈現在前端
    try:
        if request.method == "POST":
            id_ = request.POST['id']
            unit = pointBox.objects.get(id=int(id_))
            unit.isSlove = 1        #1為已解決
            unit.save()
            return HttpResponse("Successed", status=200)
        return HttpResponse("", status=405)
    except Exception as e:
        print(e, "solvePoint 函式發生問題")
        return HttpResponse('server內部發生錯誤: solvePoint()', status=400)

def test(request):
    s = '12345'
    p = s[0:3]
    return HttpResponse(p)

def searchRelatedPoint(request):
    """
    POST: county, situation

    return json list sort by popularNum
    {
        id: int
            popularNum: int
            position: [lng(float), lat(float)]
            title: str
            time: str(yyyy-MM-dd hh:mm)
    }
    """
    if request.method == "POST":
        try:
            county = request.POST['county'] #縣市名稱 三個字 ： 台北市 台東縣 ...
            situation_ = request.POST['situation'] #狀況類別
        except Exception as e:
            print(e, "searchRelatedPoint() 取得request發生問題")
            return HttpResponse('searchRelatedPoint() 取得request發生問題', status=400)
        Points = pointBox.objects.all()
        relatePointInfo = []
        if county == '全台灣':
            for p in Points:
                if int(situation_) == 0 or int(p.situation) == int(situation_):
                        relatePointInfo.append(p)
            relatePointInfo.sort(key=lambda x: x.popularNum, reverse=True)
        else:
            for p in Points:
                county_p = p.physicalAddr[2:5]
                if county_p == county:
                    if int(situation_) == 0 or int(p.situation) == int(situation_):
                        relatePointInfo.append(p)
            relatePointInfo.sort(key=lambda x: x.popularNum, reverse=True)
        returnList = []
        for p in relatePointInfo:
            coor = []
            tempS = p.coordinate.split('&')
            coor.append(float(tempS[0]))
            coor.append(float(tempS[1]))
            tempT = p.startDate.split(' ')
            time_str = tempT[0]
            time_str += ' '
            time_str += tempT[1][0:5]
            returnDict = {
                'id': p.id,
                'popularNum': p.popularNum,
                'position': coor,
                'title': p.situaName,
                'time': time_str,
            }
            returnList.append(returnDict)
        #print(returnList)
        a = HttpResponse(json.dumps(returnList), status=200)
        a.headers['Access-Control-Allow-Origin'] = '*'
        return a
        
def updateDataBase1(request):
    Points = pointBox.objects.all()
    returnList = []
    for p in Points:
        coor = []
        tempS = p.coordinate.split('&')
        coor.append(float(tempS[0]))
        coor.append(float(tempS[1]))
        returnDict = {
                'id': p.id,
                'position': coor,
            }
        returnList.append(returnDict)
    a = HttpResponse(json.dumps(returnList), status=200)
    a.headers['Access-Control-Allow-Origin'] = '*'
    return a

def updateDataBase2(request):
    if request.method == 'GET':
        jsoninput = request.GET['jsoninput']
        jsoninput_dict = json.loads(jsoninput)
        for i in range(0, len(jsoninput_dict)):
            unit = pointBox.objects.get(id=int(jsoninput_dict[i]['id']))
            unit.physicalAddr = jsoninput_dict[i]['physicalAddr']
            unit.save()
    return HttpResponse('success', status=200)

def listRelatedPoint(request):      #前端傳送一個list 裡面是一堆座標, 再從此函式回傳其在資料庫中查找到的id, 若找不到則id為0
    '''
        POST
        polyline: google polyline  (decoder: route.polyline.decode)

        return: json list sort by popularNum
        {
            id: int
            popularNum: int
            position: [lng(float), lat(float)]
            title: str
            time: str(yyyy-MM-dd hh:mm)
        }
    '''
    from routeMap import route
    if(request.method == "POST"):
        try:
            poly = request.POST['polyline']
        except Exception as e:
            print(e, "listRelatedPoint() 取得request發生問題")
            return HttpResponse('listRelatedPoint() 取得request發生問題', status=400)
        polyList = route.polyline.decode(poly)
        ##計算每個座標點與前一個座標點的歐式距離 若點A與點B超過50公尺 則在A&B中間多加一個座標點 以此類推
        mostDist = 0.0005
        exPoint = []

        p = 1
        #for p in range(1, len(polyList)):
        while True:
            exPoint = polyList[p-1].copy()
            dist = math.sqrt((polyList[p][1] - exPoint[1])**2 + (polyList[p][0] - exPoint[0])**2)
            if dist >= mostDist:
                flag = dist / mostDist
                x = (polyList[p][1] - exPoint[1]) / (flag + 1)
                y = (polyList[p][0] - exPoint[0]) / (flag + 1)
                newPoint = exPoint.copy()
                for i in range(1, (int)(flag + 1)):
                    newPoint[0] += y
                    newPoint[1] += x
                    tempPoint = newPoint.copy()
                    polyList.insert(p + (i - 1), tempPoint)
            p += 1
            if p == len(polyList):
                break

        ##
        relatePointID = searchAdjacencyPoint(polyList, 0.0003)
        relatePointInfo = []        #object of list
        Points = pointBox.objects.all()
        for p in Points:
            for rpID in relatePointID:
                if p.id == rpID:
                    relatePointInfo.append(p)
        # To sort the list in place...
        relatePointInfo.sort(key=lambda x: x.popularNum, reverse=True)
        returnList = []
        for p in relatePointInfo:
            coor = []
            tempS = p.coordinate.split('&')
            coor.append(float(tempS[0]))
            coor.append(float(tempS[1]))
            tempT = p.startDate.split(' ')
            time_str = tempT[0]
            time_str += ' '
            time_str += tempT[1][0:5]
            returnDict = {
                'id': p.id,
                'popularNum': p.popularNum,
                'position': coor,
                'title': p.situaName,
                'time': time_str,
            }
            returnList.append(returnDict)
        a = HttpResponse(json.dumps(returnList), status=200)
        a.headers['Access-Control-Allow-Origin'] = '*'
        return a

def getPointInfo(request):      #透過id查詢Datebase 回傳相關資料給前端(透過json format)
    try:
        if request.method == "GET":
            id_ = request.GET['id']
            unit = pointBox.objects.get(id=id_)
            time_str = unit.startDate[0:16]
            #print(type(unit.picLink))
            str_temp = "{}".format(unit.picLink)
            returnDict = {
                'id':id_,
                'posterName' : unit.posterName,
                'situaName'  : unit.situaName,
                'coordinate' : unit.coordinate,
                'remark'     : unit.remark,
                'popularNum' : unit.popularNum,
                'isSlove'    : unit.isSlove,
                'startDate'  : time_str,
                'endDate'    : unit.endDate,
                'picLink'    : str_temp
            }
            a =  HttpResponse(json.dumps(returnDict) ,status=200)
            a.headers['Access-Control-Allow-Origin'] = '*'
            return a
        return HttpResponse("", status=405)
    except Exception as e:
        print(e, "getPointInfo 函式發生問題")
        return HttpResponse('server內部發生錯誤: getPointInfo()', status=400)

def getAllPoints(request):
    '''
        get all point infomation
        return json list of 
        {
            id: int
            popularNum: int
            position: [lng(float), lat(float)]
            title: str
            time: str(yyyy-MM-dd hh:mm)
        }
    '''
    Points = pointBox.objects.values('id','popularNum','coordinate','situaName','startDate', 'physicalAddr', 'situation').order_by('-popularNum').all()
    return HttpResponse(json.dumps(
        [{
            'id': p['id'],
            'popularNum': p['popularNum'],
            'position': [float(i) for i in p['coordinate'].split('&')],
            'title': p['situaName'],
            'time': p['startDate'][:16],
            'physicalAddr': p['physicalAddr'],
            'situation': p['situation'],
        } for p in Points]
    ))

    
def searchAdjacencyPoint(pointList, mostDist): 
    """
        input: 一組float 的 point list
        retunr: 一組int 的 point id from database
        回傳一組List id。Database與pointList裡座標相近的事件點
        經緯度若差0.0001 則實際差10公尺 目前設計為30公尺內之事件點可被回傳
    """
    Points = pointBox.objects.all() #所有使用者上傳的全部事件點
    dbCoordinate = []   #type float of list: [id1, x1, y1, id2, x2, y2, ...] 先緯度 再精度
    for p in Points:
        tempS = p.coordinate.split('&')
        tempF = []
        dbCoordinate.append(p.id)
        dbCoordinate.append(float(tempS[0]))
        dbCoordinate.append(float(tempS[1]))
    AdjP_ID_list = []   #最後要回傳的一組list
    #
    #   鄰近座標 演算法 歐式距離(目前先用跟整個DB point掃描的方式 之後改)
    index_listUser = 0
    for i in range(0, len(pointList)):
        index_db = 0
        for j in range(0, int(len(dbCoordinate)/3)):
            dist = math.sqrt((pointList[i][1] - dbCoordinate[index_db+1])**2 + (pointList[i][0] - dbCoordinate[index_db+2])**2)
            if dist <= mostDist:
                AdjP_ID_list.append(dbCoordinate[index_db])
            index_db += 3    
    set_adj = set(AdjP_ID_list) #刪掉重複的id
    AdjP_ID_list.clear()
    AdjP_ID_list = list(set_adj)
    return AdjP_ID_list



