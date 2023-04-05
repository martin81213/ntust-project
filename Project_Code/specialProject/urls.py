"""specialProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from routeMap import views
from routeMap import mapAPI
from routeMap import analysisAPI

urlpatterns = [
    path('', views.home),
    path('admin/', admin.site.urls),
    path('map/', views.map_page),

    # event api
    path('insertPoint', views.insertPoint),
    path('searchRelatedPoint',views.searchRelatedPoint),
    path('modifyPopularNum', views.modifyPopularNum),
    path('solvePoint', views.solvePoint),
    path('listRelatedPoint', views.listRelatedPoint), 
    path('getPointInfo', views.getPointInfo),
    path('getAllPoints', views.getAllPoints),

    # map api
    path('box', mapAPI.box),
    path('dataImg', mapAPI.getImg),
    path('curve', mapAPI.curve),
    path('dangerous', mapAPI.cal_dangerous),
    path('road_block', mapAPI.road_block),

    # analysis page
    path('analysis', analysisAPI.analysis_page),
    path('summary',analysisAPI.summary),

    #test
    path('test', views.test),
    path('updateDataBase1', views.updateDataBase1),
    path('updateDataBase2', views.updateDataBase2),
    
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
