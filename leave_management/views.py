from django.shortcuts import render
from django.http import HttpResponse
from .models import Employee

def hello(request):
    employee = Employee.objects.first() #สร้าง SQL แล้วคืนพนักงานในแถวแรก
    if employee:
        return HttpResponse(f"Hello, {employee.name}") #กรณีที่มีชื่อในตาราง จะแสดงชื่อออกมาบนเว็บ
    return HttpResponse("Hello, ไม่พบข้อมูลพนักงาน") #กรณีที่ไม่มีชื่ออยู่ในตาราง จะแสดงข้อความนี้บนเว็บ

# Create your views here.
