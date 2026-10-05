from django.shortcuts import render
from django.http import HttpResponse
from .models import Employee

def hello(request):
    employee = Employee.objects.first()
    if employee:
        return HttpResponse(f"Hello, {employee.name}")
    return HttpResponse("Hello, ไม่พบข้อมูลพนักงาน")

# Create your views here.
