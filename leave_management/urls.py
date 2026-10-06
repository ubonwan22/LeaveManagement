from django.urls import path #path app
from . import views

urlpatterns = [
    path('', views.hello, name='hello'), #URL ว่างให้เรียกฟังก์ชัน hello ส่วน name='hello' ใช้อ้างอิงในโค้ตอื่น
]