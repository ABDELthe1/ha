from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Utilisateur, Patient, Medecin, RendezVous


@admin.register(Utilisateur)
class UtilisateurAdmin(BaseUserAdmin):
    """
    Administration des utilisateurs (Secrétaires et Médecins)
    """
    list_display = (
        'username', 'nom_complet', 'role', 'actif', 
        'date_creation_compte', 'last_login'
    )
    list_filter = ('role', 'actif', 'date_creation_compte', 'is_staff')
    search_fields = ('username', 'nom_complet', 'email')
    ordering = ('nom_complet',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Informations Cabinet', {
            'fields': ('role', 'nom_complet', 'actif')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Informations Cabinet', {
            'fields': ('role', 'nom_complet', 'actif')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ('date_creation_compte',)
        return self.readonly_fields


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    """
    Administration des patients
    """
    list_display = (
        'nom', 'prenom', 'telephone', 'email', 
        'date_naissance', 'nb_rdv', 'date_creation_fiche'
    )
    list_filter = ('date_creation_fiche', 'date_naissance')
    search_fields = ('nom', 'prenom', 'telephone', 'email')
    ordering = ('nom', 'prenom')
    date_hierarchy = 'date_creation_fiche'
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('nom', 'prenom', 'date_naissance')
        }),
        ('Contact', {
            'fields': ('telephone', 'email', 'adresse')
        }),
        ('Notes', {
            'fields': ('notes_administratives',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('date_creation_fiche',)
    
    def nb_rdv(self, obj):
        """Affiche le nombre de rendez-vous du patient"""
        count = obj.rendezvous_set.count()
        if count > 0:
            url = reverse('admin:gestion_rdv_rendezvous_changelist')
            return format_html(
                '<a href="{}?patient__id__exact={}">{} RDV</a>',
                url, obj.pk, count
            )
        return "0 RDV"
    nb_rdv.short_description = "Nombre de RDV"


class RendezVousInline(admin.TabularInline):
    """
    Inline pour afficher les rendez-vous dans l'admin des médecins
    """
    model = RendezVous
    extra = 0
    fields = ('patient', 'date_heure_debut', 'duree_minutes', 'statut_rdv')
    readonly_fields = ('patient', 'date_heure_debut')
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Medecin)
class MedecinAdmin(admin.ModelAdmin):
    """
    Administration des médecins
    """
    list_display = (
        'get_nom_complet', 'specialite', 'telephone_professionnel',
        'get_actif', 'nb_rdv_planifies'
    )
    list_filter = ('specialite', 'utilisateur__actif')
    search_fields = (
        'utilisateur__nom_complet', 'specialite', 
        'telephone_professionnel'
    )
    ordering = ('utilisateur__nom_complet',)
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('utilisateur',)
        }),
        ('Informations professionnelles', {
            'fields': ('specialite', 'telephone_professionnel')
        }),
        ('Horaires', {
            'fields': ('horaires_disponibilite',),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [RendezVousInline]
    
    def get_nom_complet(self, obj):
        return obj.utilisateur.nom_complet
    get_nom_complet.short_description = "Nom complet"
    get_nom_complet.admin_order_field = 'utilisateur__nom_complet'
    
    def get_actif(self, obj):
        if obj.utilisateur.actif:
            return format_html(
                '<span style="color: green;">✓ Actif</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Inactif</span>'
        )
    get_actif.short_description = "Statut"
    get_actif.admin_order_field = 'utilisateur__actif'
    
    def nb_rdv_planifies(self, obj):
        """Affiche le nombre de rendez-vous planifiés"""
        count = obj.rendezvous_set.filter(
            statut_rdv__in=['PLANIFIE', 'CONFIRME']
        ).count()
        if count > 0:
            url = reverse('admin:gestion_rdv_rendezvous_changelist')
            return format_html(
                '<a href="{}?medecin__id__exact={}&statut_rdv__in=PLANIFIE,CONFIRME">{} RDV</a>',
                url, obj.pk, count
            )
        return "0 RDV"
    nb_rdv_planifies.short_description = "RDV planifiés"


@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):
    """
    Administration des rendez-vous
    """
    list_display = (
        'get_patient_nom', 'get_medecin_nom', 'date_heure_debut',
        'duree_minutes', 'type_consultation', 'statut_rdv_colored',
        'get_secretaire'
    )
    list_filter = (
        'statut_rdv', 'type_consultation', 'medecin__specialite',
        'date_heure_debut', 'date_creation_rdv'
    )
    search_fields = (
        'patient__nom', 'patient__prenom',
        'medecin__utilisateur__nom_complet',
        'notes_rdv'
    )
    ordering = ('-date_heure_debut',)
    date_hierarchy = 'date_heure_debut'
    
    fieldsets = (
        ('Rendez-vous', {
            'fields': (
                'patient', 'medecin', 'date_heure_debut', 
                'duree_minutes', 'type_consultation'
            )
        }),
        ('Statut et notes', {
            'fields': ('statut_rdv', 'notes_rdv')
        }),
        ('Traçabilité', {
            'fields': (
                'secretaire_creation', 'date_creation_rdv', 
                'date_derniere_maj_rdv'
            ),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = (
        'date_creation_rdv', 'date_derniere_maj_rdv'
    )
    
    def get_patient_nom(self, obj):
        return f"{obj.patient.nom} {obj.patient.prenom}"
    get_patient_nom.short_description = "Patient"
    get_patient_nom.admin_order_field = 'patient__nom'
    
    def get_medecin_nom(self, obj):
        return f"Dr. {obj.medecin.utilisateur.nom_complet}"
    get_medecin_nom.short_description = "Médecin"
    get_medecin_nom.admin_order_field = 'medecin__utilisateur__nom_complet'
    
    def get_secretaire(self, obj):
        return obj.secretaire_creation.nom_complet
    get_secretaire.short_description = "Créé par"
    get_secretaire.admin_order_field = 'secretaire_creation__nom_complet'
    
    def statut_rdv_colored(self, obj):
        """Affiche le statut avec une couleur"""
        colors = {
            'PLANIFIE': 'orange',
            'CONFIRME': 'green',
            'ANNULE': 'red',
            'TERMINE': 'blue'
        }
        color = colors.get(obj.statut_rdv, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_statut_rdv_display()
        )
    statut_rdv_colored.short_description = "Statut"
    statut_rdv_colored.admin_order_field = 'statut_rdv'
    
    def get_queryset(self, request):
        """Optimise les requêtes"""
        return super().get_queryset(request).select_related(
            'patient', 'medecin__utilisateur', 'secretaire_creation'
        )


# Configuration de l'interface d'administration
admin.site.site_header = "Administration Cabinet Médical"
admin.site.site_title = "Cabinet Médical"
admin.site.index_title = "Gestion du Cabinet Médical"