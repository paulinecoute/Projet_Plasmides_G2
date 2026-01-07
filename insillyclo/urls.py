# insillyclo/urls.py

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
    # administrateur
    path('admin/', admin.site.urls),

    # pages web
    path('', views.home, name='home'),
    path('create-template/', views.create_template, name='create_template'),
    path('simulation/', views.simulation, name='simulation'),
    path('search/', views.search, name='search'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='biolib/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('create_template/', views.create_template, name='create_template'),

    # autre
    path('download_empty_template/', views.download_empty_template, name='download_empty_template'),
]

