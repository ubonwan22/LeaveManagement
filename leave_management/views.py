from django.shortcuts import render
from django.http import HttpResponse

def hello(request):
    return HttpResponse("Hello, อูซอก")

# Create your views here.
