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

    # gestion des templates 
    # le menu (choix entre créer ou télécharger)
    path('create_template/', views.create_template, name='create_template'),
    # le formulaire de création 
    path('create_template/new/', views.template_create_view, name='template_create_view'),

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
