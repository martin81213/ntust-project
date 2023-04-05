from routeMap.analyze import utilize
from django.http import HttpResponse
import json
from django.shortcuts import render

def analysis_page(request):
    '''
        Render analysis.html
    '''
    return render(request,'analysis.html')

def summary(request):
    '''
        Get analysis data
        Method: GET \n
        Parameter: None \n
        Response: list of [city, count] e.g. [['高雄市', 46001], ['臺中市', 43894], ... ]
    '''
    if request.method == "GET":
        # return 
        resp = HttpResponse(json.dumps(utilize.city_count))
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp