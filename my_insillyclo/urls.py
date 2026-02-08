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
    path('search/', views.search_view, name='search'),

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

    # Demande de publication Template
    path('template/<int:pk>/request-publish/', views.request_template_publication, name='request_template_publication'),

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
    path('simulation/<int:simulation_id>/save/', views.save_generated_plasmid, name='save_generated_plasmid'),

    # --- NOUVEAU : Suppression et Partage Simulation ---
    path('simulation/<int:pk>/delete/', views.delete_simulation, name='delete_simulation'),
    path('simulation/<int:pk>/share/', views.share_simulation_team, name='share_simulation_team'),
    # ---------------------------------------------------

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
    # 1. GESTION DES COLLECTIONS (Perso & Équipe unifiés)
    # ============================================================
    path('collections/', views.plasmid_collection_list, name='plasmid_collection_list'),

    path('collections/create/', views.collection_create, name='collection_create'),

    path('collections/<int:pk>/', views.plasmid_collection_detail, name='plasmid_collection_detail'),

    path('collections/<int:pk>/edit/', views.collection_update, name='collection_update'),

    # Suppression
    path('collections/<int:pk>/delete/', views.plasmid_collection_delete, name='plasmid_collection_delete'),

    # Demande de publication
    path('collections/<int:pk>/publish/', views.request_publication, name='request_publication'),


    # ============================================================
    # 2. ACTIONS SUR LE CONTENU DES COLLECTIONS
    # ============================================================

    path('collections/<int:collection_id>/upload/', views.plasmid_upload, name='plasmid_upload'),

    path('collections/<int:collection_id>/remove/<int:plasmid_id>/', views.remove_plasmid_from_collection, name='remove_plasmid_from_collection'),


    # ============================================================
    # 3. GESTION DES PLASMIDES INDIVIDUELS
    # ============================================================

    # Visualisation (GenBank, carte, etc.)
    path('plasmids/<int:plasmid_id>/', views.plasmid_visualize, name='plasmid_visualize'),

    # Édition (Annotations, Séquence)
    path('plasmids/<int:pk>/edit/', views.plasmid_edit, name='plasmid_edit'),

    # Copier un plasmide (depuis une collection publique/équipe vers mes collections)
    path('plasmids/<int:pk>/copy/', views.plasmid_copy, name='plasmid_copy'),

    # ============================================================
    # CORRESPONDANCES (UTILISATEUR)
    # ============================================================

    path("correspondences/", views.correspondences_view, name="correspondences"),
    path("correspondences/upload/", views.correspondence_upload, name="correspondence_upload"),
    path('correspondences/<int:pk>/', views.correspondence_detail, name='correspondence_detail'),
    path("correspondences/<int:correspondence_id>/view/", views.correspondence_view_file, name="correspondence_view_file"),
    path("correspondences/<int:correspondence_id>/attach/", views.correspondence_attach_file, name="correspondence_attach_file"),
    path("correspondences/<int:correspondence_id>/remove-file/", views.correspondence_remove_file, name="correspondence_remove_file"),
    path("correspondences/<int:correspondence_id>/delete/", views.correspondence_delete, name="correspondence_delete"),
    path("choose-team-for-correspondences/", views.choose_team_for_correspondences, name="choose_team_for_correspondences"),
    path('correspondence/<int:pk>/request-publication/', views.correspondence_request_publication, name='correspondence_request_publication'),
    path('correspondence/', views.correspondence_list, name='correspondence_list'),
    path('correspondence/new/', views.correspondence_create, name='correspondence_create'),

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

    # ============================================================
    # ACTIONS ADMIN
    # ============================================================
    path('admin-panel/requests/', views.admin_publication_list, name='admin_publication_list'),

    # Collections
    path('admin-panel/requests/<int:pk>/approve/', views.admin_approve_collection, name='admin_approve_collection'),
    path('admin-panel/requests/<int:pk>/reject/', views.admin_reject_collection, name='admin_reject_collection'),

    # Tables de correspondance
    path('admin-panel/correspondence/<int:pk>/review/', views.admin_correspondence_review, name='admin_correspondence_review'),
    path('admin-panel/correspondence/<int:pk>/approve/', views.admin_approve_correspondence, name='admin_approve_correspondence'),
    path('admin-panel/correspondence/<int:pk>/reject/', views.admin_reject_correspondence, name='admin_reject_correspondence'),

    # Templates
    path('admin-panel/templates/<int:pk>/approve/', views.admin_approve_template, name='admin_approve_template'),
    path('admin-panel/templates/<int:pk>/reject/', views.admin_reject_template, name='admin_reject_template'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
