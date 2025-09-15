from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

# Create your views here.
def inicio(request):
    return render(request,'index.html')

def grafica(request):
    return render(request,'graficar.html')

def login(request):
    return render(request,'login.html')