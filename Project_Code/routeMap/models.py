from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.
class pointBox(models.Model):
    posterName = models.CharField(max_length=15, null=True)        # nickname of the poster
    coordinate = models.CharField(max_length=60)        ## every point's longitude and latitude
                                                        # format: 經度&緯度
    situation = models.IntegerField()                   # 0 可代表路障, 1 可代表車道問題
    remark = models.TextField(max_length=150,blank=True)           # 口語化的註記
    popularNum = models.IntegerField(default=0)         # 推廣值 0 ~ 100 數值越高越熱門 
    picLink = models.ImageField(null=True, blank=True, upload_to="media/images/")                       # 未來圖片上傳時可作之連結
    isSlove = models.IntegerField(default=0)            # 1代表已解決,0代表尚未解決之事件
    startDate = models.CharField(max_length=40)         ##日期，之後可以拿來製作時效問題
    endDate = models.CharField(max_length=40)           # format: YYYY&MM&DD
    situaName = models.CharField(max_length=20, blank=False, null=True) #事件名稱，共使用者自行定義
    physicalAddr = models.CharField(max_length=30, null=True, blank=True)
    def __str__(self):
        return self.situaName
     
class HELLOBOX(models.Model):
    hello = models.CharField(max_length=50)