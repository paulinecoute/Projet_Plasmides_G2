from django.contrib import admin
from django.urls import path
from biolib import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # administration
    path('admin/', admin.site.urls),

    # pages principales
    path('', views.home, name='home'),
    
    # menu templates
    path('template/', views.template, name='template'),
    
    path('simulation/', views.simulation, name='simulation'),

    # télécharger doc excel
    path('template/export/<int:template_id>/', views.export_template_excel, name='export_template_excel'),

    # gestion templates
    path('create_template/new/', views.create_template, name='create_template'),

    # page résultats détaillé
    path('simulation_result/', views.simulation_result, name='simulation_result'),

    # template details
    path('template/<int:pk>/details/', views.template_detail, name='template_detail'),

    # --- NOUVELLE LIGNE AJOUTÉE ICI (Suppression) ---
    path('template/<int:pk>/delete/', views.delete_template, name='delete_template'),
    # -----------------------------------------------

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
    
    # simulations
    path('simulation/new/', views.create_simulation, name='create_simulation'),
    path('simulation/<int:pk>/', views.simulation_result, name='simulation_result'),
    path('simulations/', views.simulation_list, name='simulation_list'),
    path('simulation/demo/', views.simulation_result, name='simulation_demo'),
    path('simulation/<int:pk>/csv/', views.download_simulation_csv, name='download_simulation_csv'),
    path('simulation/<int:pk>/download_zip/', views.download_simulation_zip, name='download_simulation_zip'),

    # équipes
    path('teams/', views.team_list, name='teams'),
    path('teams/create/', views.team_create, name='team_create'),
    path('teams/<int:team_id>/', views.team_detail, name='team_detail'),
    path('teams/<int:team_id>/manage/', views.team_manage_members, name='team_manage_members'),
    path(
        'teams/<int:team_id>/remove/<int:user_id>/',
        views.team_remove_member,
        name='team_remove_member'
    ),
    path(
        'teams/<int:team_id>/delete/',
        views.team_delete,
        name='team_delete'
    ),
    path(
        'teams/<int:team_id>/leave/',
        views.team_leave,
        name='team_leave'
    ),
    path(
        'teams/<int:team_id>/change_leader/<int:user_id>/',
        views.team_change_leader,
        name='team_change_leader'
    ),
]
