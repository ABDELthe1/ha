from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from datetime import datetime, time
import json


class Utilisateur(AbstractUser):
    """
    Modèle utilisateur personnalisé pour gérer secrétaires et médecins
    """
    ROLE_CHOICES = [
        ('SECRETAIRE', 'Secrétaire'),
        ('MEDECIN', 'Médecin'),
    ]
    
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='SECRETAIRE',
        verbose_name='Rôle'
    )
    nom_complet = models.CharField(
        max_length=100, 
        verbose_name='Nom complet'
    )
    actif = models.BooleanField(
        default=True, 
        verbose_name='Compte actif'
    )
    date_creation_compte = models.DateTimeField(
        auto_now_add=True, 
        verbose_name='Date de création du compte'
    )
    
    # Fix reverse accessor conflicts
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='utilisateur_set',
        related_query_name='utilisateur',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='utilisateur_set',
        related_query_name='utilisateur',
    )
    
    class Meta:
        verbose_name = 'Utilisateur'
        verbose_name_plural = 'Utilisateurs'
    
    def __str__(self):
        return f"{self.nom_complet} ({self.get_role_display()})"


class Medecin(models.Model):
    """
    Informations spécifiques aux médecins
    """
    utilisateur = models.OneToOneField(
        Utilisateur, 
        on_delete=models.CASCADE, 
        primary_key=True,
        limit_choices_to={'role': 'MEDECIN'}
    )
    specialite = models.CharField(
        max_length=100, 
        verbose_name='Spécialité médicale'
    )
    telephone_professionnel = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Le numéro de téléphone doit être au format valide."
        )],
        verbose_name='Téléphone professionnel'
    )
    horaires_disponibilite = models.TextField(
        blank=True, 
        null=True,
        help_text="Horaires de disponibilité au format JSON",
        verbose_name='Horaires de disponibilité'
    )
    
    class Meta:
        verbose_name = 'Médecin'
        verbose_name_plural = 'Médecins'
    
    def __str__(self):
        return f"Dr. {self.utilisateur.nom_complet} - {self.specialite}"
    
    def get_horaires(self):
        """
        Retourne les horaires sous forme de dictionnaire Python
        """
        if self.horaires_disponibilite:
            try:
                return json.loads(self.horaires_disponibilite)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_horaires(self, horaires_dict):
        """
        Sauvegarde les horaires au format JSON
        """
        self.horaires_disponibilite = json.dumps(horaires_dict, ensure_ascii=False)


class Patient(models.Model):
    """
    Informations des patients du cabinet
    """
    nom = models.CharField(
        max_length=50, 
        verbose_name='Nom'
    )
    prenom = models.CharField(
        max_length=50, 
        verbose_name='Prénom'
    )
    date_naissance = models.DateField(
        blank=True, 
        null=True,
        verbose_name='Date de naissance'
    )
    telephone = models.CharField(
        max_length=20,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="Le numéro de téléphone doit être au format valide."
        )],
        verbose_name='Téléphone'
    )
    adresse = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Adresse'
    )
    email = models.EmailField(
        blank=True, 
        null=True,
        verbose_name='Email'
    )
    notes_administratives = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Notes administratives'
    )
    date_creation_fiche = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date de création de la fiche'
    )
    
    class Meta:
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'
        indexes = [
            models.Index(fields=['nom', 'prenom']),
            models.Index(fields=['telephone']),
        ]
    
    def __str__(self):
        return f"{self.nom} {self.prenom}"
    
    def get_identite(self):
        """
        Retourne l'identité complète du patient
        """
        return f"{self.nom} {self.prenom}"


class RendezVous(models.Model):
    """
    Rendez-vous entre patients et médecins
    """
    STATUT_CHOICES = [
        ('PLANIFIE', 'Planifié'),
        ('CONFIRME', 'Confirmé'),
        ('ANNULE', 'Annulé'),
        ('TERMINE', 'Terminé'),
    ]
    
    TYPE_CONSULTATION_CHOICES = [
        ('CONSULTATION', 'Consultation'),
        ('SUIVI', 'Suivi'),
        ('URGENCE', 'Urgence'),
        ('VISITE_DOMICILE', 'Visite à domicile'),
        ('AUTRE', 'Autre'),
    ]
    
    patient = models.ForeignKey(
        Patient, 
        on_delete=models.RESTRICT,
        verbose_name='Patient'
    )
    medecin = models.ForeignKey(
        Medecin, 
        on_delete=models.RESTRICT,
        verbose_name='Médecin'
    )
    secretaire_creation = models.ForeignKey(
        Utilisateur,
        on_delete=models.RESTRICT,
        limit_choices_to={'role': 'SECRETAIRE'},
        verbose_name='Secrétaire responsable'
    )
    date_heure_debut = models.DateTimeField(
        verbose_name='Date et heure de début'
    )
    duree_minutes = models.PositiveIntegerField(
        default=30,
        verbose_name='Durée en minutes'
    )
    type_consultation = models.CharField(
        max_length=50,
        choices=TYPE_CONSULTATION_CHOICES,
        default='CONSULTATION',
        verbose_name='Type de consultation'
    )
    statut_rdv = models.CharField(
        max_length=30,
        choices=STATUT_CHOICES,
        default='PLANIFIE',
        verbose_name='Statut du rendez-vous'
    )
    notes_rdv = models.TextField(
        blank=True, 
        null=True,
        verbose_name='Notes du rendez-vous'
    )
    date_creation_rdv = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Date de création du RDV'
    )
    date_derniere_maj_rdv = models.DateTimeField(
        auto_now=True,
        verbose_name='Dernière mise à jour'
    )
    
    class Meta:
        verbose_name = 'Rendez-vous'
        verbose_name_plural = 'Rendez-vous'
        constraints = [
            models.UniqueConstraint(
                fields=['medecin', 'date_heure_debut'],
                name='unique_medecin_creneau'
            )
        ]
        indexes = [
            models.Index(fields=['patient']),
            models.Index(fields=['medecin', 'date_heure_debut']),
            models.Index(fields=['statut_rdv']),
            models.Index(fields=['date_heure_debut']),
        ]
        ordering = ['date_heure_debut']
    
    def __str__(self):
        return f"RDV {self.patient} - Dr. {self.medecin.utilisateur.nom_complet} le {self.date_heure_debut.strftime('%d/%m/%Y %H:%M')}"
    
    @property
    def date_heure_fin(self):
        """
        Calcule la date et heure de fin du rendez-vous
        """
        from datetime import timedelta
        return self.date_heure_debut + timedelta(minutes=self.duree_minutes)
    
    def is_conflit_avec(self, autre_rdv):
        """
        Vérifie s'il y a conflit avec un autre rendez-vous
        """
        if self.medecin != autre_rdv.medecin:
            return False
        
        # Vérifier les chevauchements
        debut1, fin1 = self.date_heure_debut, self.date_heure_fin
        debut2, fin2 = autre_rdv.date_heure_debut, autre_rdv.date_heure_fin
        
        return not (fin1 <= debut2 or fin2 <= debut1)
    
    def clean(self):
        """
        Validation personnalisée du modèle
        """
        from django.core.exceptions import ValidationError
        from datetime import datetime
        
        # Vérifier que la date n'est pas dans le passé
        if self.date_heure_debut and self.date_heure_debut < datetime.now():
            if not self.pk:  # Nouveau rendez-vous seulement
                raise ValidationError("La date du rendez-vous ne peut pas être dans le passé.")
        
        # Vérifier les conflits avec d'autres rendez-vous
        if self.medecin and self.date_heure_debut:
            conflits = RendezVous.objects.filter(
                medecin=self.medecin,
                statut_rdv__in=['PLANIFIE', 'CONFIRME']
            ).exclude(pk=self.pk)
            
            for rdv in conflits:
                if self.is_conflit_avec(rdv):
                    raise ValidationError(
                        f"Conflit détecté avec le rendez-vous de {rdv.patient} "
                        f"le {rdv.date_heure_debut.strftime('%d/%m/%Y %H:%M')}"
                    )
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)