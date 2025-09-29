from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

# Create your views here.
def inicio(request):
    return render(request,'index.html')

def resolver(request):
    return render(request,'resolver.html')

def grafica(request):
    return render(request,'graficar.html')

def login_regis(request):
    return render(request,'login.html')