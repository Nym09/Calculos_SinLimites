from django.urls import path
from . import views

urlpatterns = [
       path('', views.inicio, name='index'),
       path('resolver/', views.resolver, name='resolver'),
       path('graficar/', views.grafica,name='graficar'),
       path('login', views.login_regis, name='login'),
]