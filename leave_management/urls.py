from django.urls import path #path app
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', views.AppLoginView.as_view(
        template_name='leave_management/login.html',
        redirect_authenticated_user=True), name='login'),
    path('logout/', views.AppLogoutView.as_view(), name='logout'),  # ต้องเรียกด้วย POST
    path('', views.dashboard, name='dashboard'),
    path('hello/', views.hello, name='hello'), 
    path('requests/', views.request_list, name='request_list'),
    path('requests/new/', views.request_create, name='request_create'),
    path('requests/<int:pk>/decide/', views.request_decide, name='request_decide'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('holidays/', views.holiday_list, name='holiday_list'),
]