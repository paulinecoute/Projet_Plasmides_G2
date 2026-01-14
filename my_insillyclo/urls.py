# my_insillyclo/urls.py

"""
URL configuration for insillyclo project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from biolib import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # administration
    path('admin/', admin.site.urls),

    # pages principales
    path('', views.home, name='home'),
    path('template/', views.template, name='template'),
    path('simulation/', views.simulation, name='simulation'),

    # page creation de templates
    path('create_template/', views.create_template, name='create_template'),

    # page résultats détaillé
    path('simulation_result/', views.simulation_result, name='simulation_result'),
    path('template_detail/', views.template_detail, name='template_detail'),

    # authentification
    path('signup/', views.signup, name='signup'),
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='biolib/login.html'),
        name='login'
    ),
    path(
        'logout/',
        auth_views.LogoutView.as_view(),
        name='logout'
    ),

    # espace personnel
    path('dashboard/', views.dashboard, name='dashboard'),
]
