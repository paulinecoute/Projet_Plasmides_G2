from django.contrib import admin
from django.urls import path, include
from biolib import views
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # administration
    path('admin/', admin.site.urls),

    # pages principales
    path('', views.home, name='home'),
    path('search/', views.search_view, name='search'), # <--- NOUVELLE ROUTE RECHERCHE

    # menu templates
    path('template/', views.template, name='template'),

    path('simulation/', views.simulation_list, name='simulation_list'),

    # télécharger doc excel
    path('template/export/<int:template_id>/', views.export_template_excel, name='export_template_excel'),

    # gestion templates
    path('create_template/new/', views.create_template, name='create_template'),

    # page résultats détaillé
    path('simulation_result/', views.simulation_result, name='simulation_result'),

    # template details
    path('template/<int:pk>/details/', views.template_detail, name='template_detail'),

    # suppression template
    path('template/<int:pk>/delete/', views.delete_template, name='delete_template'),

    path(
        "teams/<int:team_id>/templates/",
        views.team_templates,
        name="team_templates"
    ),

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


    path('library/', views.plasmid_collection_list, name='plasmid_collection_list'),
    path('library/<int:pk>/', views.plasmid_collection_detail, name='plasmid_collection_detail'),
    path('plasmide_visualize/<int:plasmid_id>/', views.plasmid_visualize, name='plasmid_visualize'),


    # simulations
    path('simulation/new/', views.create_simulation, name='create_simulation'),
    path('simulation/<int:pk>/', views.simulation_result, name='simulation_result'),
    path('simulations/', views.simulation_list, name='simulation_list'),
    path('simulation/demo/', views.simulation_result, name='simulation_demo'),
    path('simulation/<int:pk>/csv/', views.download_simulation_csv, name='download_simulation_csv'),
    path('simulation/<int:pk>/download_zip/', views.download_simulation_zip, name='download_simulation_zip'),
    path('simulation/<int:pk>/download_file/<str:filename>/', views.download_specific_file, name='download_specific_file'),
    path('simulation/<int:pk>/update_gel/', views.update_simulation_gel, name='update_simulation_gel'),
    path("teams/<int:team_id>/simulations/", views.team_simulations, name="team_simulations"),

    # ============================================================
    # ESPACE PERSONNEL
    # ============================================================

    path('dashboard/', views.dashboard, name='dashboard'),
    
    # ============================================================
    # ÉQUIPES
    # ============================================================

    path("teams/", views.team_list, name="teams"),
    path("teams/create/", views.team_create, name="team_create"),
    path("teams/<int:team_id>/", views.team_detail, name="team_detail"),
    path("teams/<int:team_id>/manage/", views.team_manage_members, name="team_manage_members"),
    path("teams/<int:team_id>/remove/<int:user_id>/", views.team_remove_member, name="team_remove_member"),
    path("teams/<int:team_id>/delete/", views.team_delete, name="team_delete"),
    path("teams/<int:team_id>/leave/", views.team_leave, name="team_leave"),
    path("teams/<int:team_id>/change_leader/<int:user_id>/", views.team_change_leader, name="team_change_leader"),


    # ============================================================
    # COLLECTIONS (UTILISATEUR)
    # ============================================================

    path("collections/", views.collections_view, name="collections"),
    path("collections/new/", views.collection_create, name="collection_create"),
    path("collections/<int:collection_id>/", views.collection_detail, name="collection_detail"),
    path("collections/<int:collection_id>/upload/", views.plasmid_upload, name="plasmid_upload"),
    path("collections/<int:collection_id>/delete/", views.collection_delete, name="collection_delete"),
    path("plasmids/<int:plasmid_id>/delete/", views.plasmid_delete, name="plasmid_delete"),

    # ============================================================
    # COLLECTIONS (ÉQUIPE)
    # ============================================================

    path("teams/<int:team_id>/collections/", views.team_collections, name="team_collections"),
    path("teams/<int:team_id>/collections/create/", views.team_collection_create, name="team_collection_create"),
    path("teams/<int:team_id>/collections/<int:collection_id>/", views.team_collection_detail, name="team_collection_detail"),
    path("plasmids/teams/", views.choose_team_for_plasmids, name="choose_team_for_plasmids"),

    # ============================================================
    # CORRESPONDANCES (UTILISATEUR)
    # ============================================================

    path("correspondences/", views.correspondences_view, name="correspondences"),
    path("correspondences/upload/", views.correspondence_upload, name="correspondence_upload"),
    path("correspondences/<int:correspondence_id>/", views.correspondence_detail, name="correspondence_detail"),
    path("correspondences/<int:correspondence_id>/view/", views.correspondence_view_file, name="correspondence_view_file"),
    path("correspondences/<int:correspondence_id>/attach/", views.correspondence_attach_file, name="correspondence_attach_file"),
    path("correspondences/<int:correspondence_id>/remove-file/", views.correspondence_remove_file, name="correspondence_remove_file"),
    path("correspondences/<int:correspondence_id>/delete/", views.correspondence_delete, name="correspondence_delete"),
    path("choose-team-for-correspondences/", views.choose_team_for_correspondences, name="choose_team_for_correspondences"),

    # ============================================================
    # CORRESPONDANCES (ÉQUIPE)
    # ============================================================

    path("teams/<int:team_id>/correspondences/", views.team_correspondences, name="team_correspondences"),
    path("teams/<int:team_id>/correspondences/create/", views.team_correspondence_create, name="team_correspondence_create"),
    path("teams/<int:team_id>/correspondences/<int:correspondence_id>/", views.team_correspondence_detail, name="team_correspondence_detail"),
    path("teams/<int:team_id>/correspondences/<int:correspondence_id>/view/", views.team_correspondence_view_file, name="team_correspondence_view_file"),
    path("teams/<int:team_id>/correspondences/<int:correspondence_id>/attach/", views.team_correspondence_attach_file, name="team_correspondence_attach_file"),
    path("teams/<int:team_id>/correspondences/<int:correspondence_id>/remove-file/", views.team_correspondence_remove_file, name="team_correspondence_remove_file"),
    path("teams/<int:team_id>/correspondences/<int:correspondence_id>/delete/", views.team_correspondence_delete, name="team_correspondence_delete"),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
