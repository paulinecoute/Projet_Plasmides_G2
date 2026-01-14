from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from biolib import views

urlpatterns = [
    # Administrateur
    path('admin/', admin.site.urls),

    # Pages principales
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),

    # Authentification (Login/Logout)
    path('login/', auth_views.LoginView.as_view(template_name='biolib/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Fonctionnalités métier
    path('create-template/', views.create_template, name='create_template'),
    path('simulation/', views.simulation, name='simulation'),
    path('search/', views.search, name='search'),

    # Outils / Téléchargements
    path('download_empty_template/', views.download_empty_template, name='download_empty_template'),
    path('download-result/', views.download_simulation_csv, name='download_simulation_csv')
]

# INDISPENSABLE pour voir les résultats de simulation (images)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
