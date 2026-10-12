from django.urls import path #path app
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('hello/', views.hello, name='hello'), 
    path('requests/', views.request_list, name='request_list'),
    path('requests/new/', views.request_create, name='request_create'),
    path('requests/<int:pk>/decide/', views.request_decide, name='request_decide'),
    path('employees/', views.employee_list, name='employee_list'),
    path('holidays/', views.holiday_list, name='holiday_list'),
]