from django.urls import path
from . import views

urlpatterns = [
       path('', views.inicio),
       path('graficar', views.grafica),
       path('login', views.login),
]