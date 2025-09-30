from django.urls import path
from . import views

urlpatterns = [
       path('', views.inicio, name='index'),
       path('resolver/', views.resolver, name='resolver'),
       path('limites/', views.grafica_limit,name='limites'),
       path('derivadas/', views.grafica_deriv,name='derivadas'),
       path('login', views.login_regis, name='login'),
]