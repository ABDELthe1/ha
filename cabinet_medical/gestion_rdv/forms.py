from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from .models import Patient, Medecin, RendezVous, Utilisateur
import json


class PatientForm(forms.ModelForm):
    """
    Formulaire pour la gestion des patients
    """
    class Meta:
        model = Patient
        fields = [
            'nom', 'prenom', 'date_naissance', 'telephone', 
            'adresse', 'email', 'notes_administratives'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du patient'
            }),
            'prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Prénom du patient'
            }),
            'date_naissance': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: 0123456789'
            }),
            'adresse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Adresse complète'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'email@exemple.com'
            }),
            'notes_administratives': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes diverses (mutuelle, allergies, etc.)'
            })
        }

    def clean_telephone(self):
        telephone = self.cleaned_data.get('telephone')
        if telephone:
            # Supprimer les espaces et caractères spéciaux
            telephone = ''.join(filter(str.isdigit, telephone.replace('+', '')))
            if len(telephone) < 9 or len(telephone) > 15:
                raise ValidationError("Le numéro de téléphone doit contenir entre 9 et 15 chiffres.")
        return telephone


class MedecinUserForm(UserCreationForm):
    """
    Formulaire pour créer un utilisateur médecin
    """
    nom_complet = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Dr. Nom Prénom'
        })
    )
    
    class Meta:
        model = Utilisateur
        fields = ('username', 'nom_complet', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom d\'utilisateur'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'MEDECIN'
        if commit:
            user.save()
        return user


class MedecinForm(forms.ModelForm):
    """
    Formulaire pour les informations spécifiques du médecin
    """
    # Champs pour les horaires (simplifié)
    lundi_debut = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    lundi_fin = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    mardi_debut = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    mardi_fin = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    mercredi_debut = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    mercredi_fin = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    jeudi_debut = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    jeudi_fin = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    vendredi_debut = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    vendredi_fin = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    samedi_debut = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )
    samedi_fin = forms.TimeField(
        required=False,
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'})
    )

    class Meta:
        model = Medecin
        fields = ['specialite', 'telephone_professionnel']
        widgets = {
            'specialite': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ex: Cardiologie, Médecine générale...'
            }),
            'telephone_professionnel': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Téléphone professionnel'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Charger les horaires existants
        if self.instance and self.instance.pk:
            horaires = self.instance.get_horaires()
            for jour in ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi']:
                if jour in horaires:
                    if 'debut' in horaires[jour]:
                        self.fields[f'{jour}_debut'].initial = horaires[jour]['debut']
                    if 'fin' in horaires[jour]:
                        self.fields[f'{jour}_fin'].initial = horaires[jour]['fin']

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Construire le dictionnaire des horaires
        horaires = {}
        for jour in ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi']:
            debut = self.cleaned_data.get(f'{jour}_debut')
            fin = self.cleaned_data.get(f'{jour}_fin')
            if debut and fin:
                horaires[jour] = {
                    'debut': debut.strftime('%H:%M'),
                    'fin': fin.strftime('%H:%M')
                }
        
        instance.set_horaires(horaires)
        
        if commit:
            instance.save()
        return instance


class RendezVousForm(forms.ModelForm):
    """
    Formulaire pour la prise de rendez-vous
    """
    class Meta:
        model = RendezVous
        fields = [
            'patient', 'medecin', 'date_heure_debut', 'duree_minutes',
            'type_consultation', 'notes_rdv'
        ]
        widgets = {
            'patient': forms.Select(attrs={
                'class': 'form-control'
            }),
            'medecin': forms.Select(attrs={
                'class': 'form-control'
            }),
            'date_heure_debut': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'duree_minutes': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '15',
                'max': '180',
                'step': '15'
            }),
            'type_consultation': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes_rdv': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Notes particulières pour ce rendez-vous'
            })
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrer les médecins actifs
        self.fields['medecin'].queryset = Medecin.objects.filter(
            utilisateur__actif=True
        ).select_related('utilisateur')
        
        # Ordonner les patients par nom
        self.fields['patient'].queryset = Patient.objects.all().order_by('nom', 'prenom')

    def clean_date_heure_debut(self):
        date_heure = self.cleaned_data.get('date_heure_debut')
        if date_heure:
            # Vérifier que la date n'est pas dans le passé (pour nouveau RDV)
            if not self.instance.pk and date_heure < datetime.now():
                raise ValidationError("La date du rendez-vous ne peut pas être dans le passé.")
            
            # Vérifier que c'est pendant les horaires d'ouverture (exemple simple)
            if date_heure.hour < 8 or date_heure.hour > 18:
                raise ValidationError("Les rendez-vous doivent être pris entre 8h et 18h.")
        
        return date_heure

    def clean(self):
        cleaned_data = super().clean()
        medecin = cleaned_data.get('medecin')
        date_heure_debut = cleaned_data.get('date_heure_debut')
        duree_minutes = cleaned_data.get('duree_minutes', 30)

        if medecin and date_heure_debut:
            # Vérifier les conflits avec d'autres rendez-vous
            date_heure_fin = date_heure_debut + timedelta(minutes=duree_minutes)
            
            conflits = RendezVous.objects.filter(
                medecin=medecin,
                statut_rdv__in=['PLANIFIE', 'CONFIRME']
            ).exclude(pk=self.instance.pk if self.instance.pk else None)

            for rdv in conflits:
                rdv_fin = rdv.date_heure_debut + timedelta(minutes=rdv.duree_minutes)
                
                # Vérifier le chevauchement
                if not (date_heure_fin <= rdv.date_heure_debut or rdv_fin <= date_heure_debut):
                    raise ValidationError(
                        f"Conflit détecté avec le rendez-vous de {rdv.patient} "
                        f"le {rdv.date_heure_debut.strftime('%d/%m/%Y à %H:%M')}"
                    )

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user and hasattr(self.user, 'role') and self.user.role == 'SECRETAIRE':
            instance.secretaire_creation = self.user
        if commit:
            instance.save()
        return instance


class RechercheForm(forms.Form):
    """
    Formulaire de recherche globale
    """
    RECHERCHE_CHOICES = [
        ('patient', 'Patients'),
        ('medecin', 'Médecins'),
        ('rdv', 'Rendez-vous'),
        ('tous', 'Tous'),
    ]
    
    query = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher...'
        }),
        label='Recherche'
    )
    
    type_recherche = forms.ChoiceField(
        choices=RECHERCHE_CHOICES,
        initial='tous',
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Type'
    )


class PlanningFilterForm(forms.Form):
    """
    Formulaire pour filtrer le planning
    """
    medecin = forms.ModelChoiceField(
        queryset=Medecin.objects.filter(utilisateur__actif=True),
        required=False,
        empty_label="Tous les médecins",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    date_debut = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_fin = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )