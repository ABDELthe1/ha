from django.urls import path
from . import views

app_name = 'gestion_rdv'

urlpatterns = [
    # Dashboard - both root and dashboard/ paths
    path('', views.dashboard, name='dashboard'),  # Handle root URL within app
    path('dashboard/', views.dashboard, name='dashboard_alt'),  # Alternative dashboard URL
    
    # Gestion des patients
    path('patients/', views.PatientListView.as_view(), name='patients_list'),
    path('patients/ajouter/', views.PatientCreateView.as_view(), name='patient_create'),
    path('patients/<int:pk>/modifier/', views.PatientUpdateView.as_view(), name='patient_update'),
    path('patients/<int:pk>/supprimer/', views.PatientDeleteView.as_view(), name='patient_delete'),
    path('patients/<int:pk>/', views.PatientDetailView.as_view(), name='patient_detail'),
    path('patients/recherche/', views.patient_search, name='patient_search'),
    
    # Gestion des médecins
    path('medecins/', views.MedecinListView.as_view(), name='medecins_list'),
    path('medecins/ajouter/', views.MedecinCreateView.as_view(), name='medecin_create'),
    path('medecins/<int:pk>/modifier/', views.MedecinUpdateView.as_view(), name='medecin_update'),
    path('medecins/<int:pk>/supprimer/', views.MedecinDeleteView.as_view(), name='medecin_delete'),
    path('medecins/<int:pk>/', views.MedecinDetailView.as_view(), name='medecin_detail'),
    
    # Gestion des rendez-vous
    path('rendez-vous/', views.RendezVousListView.as_view(), name='rdv_list'),
    path('rendez-vous/ajouter/', views.RendezVousCreateView.as_view(), name='rdv_create'),
    path('rendez-vous/<int:pk>/modifier/', views.RendezVousUpdateView.as_view(), name='rdv_update'),
    path('rendez-vous/<int:pk>/annuler/', views.rdv_cancel, name='rdv_cancel'),
    path('rendez-vous/<int:pk>/', views.RendezVousDetailView.as_view(), name='rdv_detail'),
    path('rendez-vous/recherche/', views.rdv_search, name='rdv_search'),
    
    # Planning
    path('planning/', views.planning_view, name='planning'),
    path('planning/medecin/<int:medecin_id>/', views.planning_medecin, name='planning_medecin'),
    path('planning/export/', views.export_planning_pdf, name='export_planning'),
    path('planning/medecin/<int:medecin_id>/export/', views.export_planning_medecin_pdf, name='export_planning_medecin'),
    
    # AJAX endpoints pour le planning
    path('api/creneaux-libres/', views.get_creneaux_libres, name='creneaux_libres'),
    path('api/rdv-jour/', views.get_rdv_jour, name='rdv_jour'),
    
    # Recherche globale
    path('recherche/', views.recherche_globale, name='recherche_globale'),
]