from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, timedelta, date
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import json

from .models import Patient, Medecin, RendezVous, Utilisateur
from .forms import PatientForm, MedecinForm, MedecinUserForm, RendezVousForm, RechercheForm, PlanningFilterForm


class SecretaireRequiredMixin(UserPassesTestMixin):
    """Mixin pour restreindre l'accès aux secrétaires"""
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'SECRETAIRE'


@login_required
def dashboard(request):
    """
    Page d'accueil - Dashboard adapté selon le rôle
    """
    user = request.user
    
    if user.role == 'SECRETAIRE':
        # Statistiques pour la secrétaire
        context = {
            'total_patients': Patient.objects.count(),
            'total_medecins': Medecin.objects.filter(utilisateur__actif=True).count(),
            'rdv_aujourd_hui': RendezVous.objects.filter(
                date_heure_debut__date=date.today(),
                statut_rdv__in=['PLANIFIE', 'CONFIRME']
            ).count(),
            'rdv_cette_semaine': RendezVous.objects.filter(
                date_heure_debut__week=date.today().isocalendar()[1],
                date_heure_debut__year=date.today().year,
                statut_rdv__in=['PLANIFIE', 'CONFIRME']
            ).count(),
            'derniers_rdv': RendezVous.objects.filter(
                statut_rdv__in=['PLANIFIE', 'CONFIRME']
            ).select_related('patient', 'medecin__utilisateur').order_by('date_heure_debut')[:5],
            'nouveaux_patients': Patient.objects.order_by('-date_creation_fiche')[:5]
        }
        return render(request, 'gestion_rdv/dashboard_secretaire.html', context)
    
    elif user.role == 'MEDECIN':
        # Dashboard pour le médecin
        try:
            medecin = user.medecin
            context = {
                'medecin': medecin,
                'rdv_aujourd_hui': RendezVous.objects.filter(
                    medecin=medecin,
                    date_heure_debut__date=date.today(),
                    statut_rdv__in=['PLANIFIE', 'CONFIRME']
                ).select_related('patient').order_by('date_heure_debut'),
                'rdv_semaine': RendezVous.objects.filter(
                    medecin=medecin,
                    date_heure_debut__week=date.today().isocalendar()[1],
                    date_heure_debut__year=date.today().year,
                    statut_rdv__in=['PLANIFIE', 'CONFIRME']
                ).count(),
                'prochains_rdv': RendezVous.objects.filter(
                    medecin=medecin,
                    date_heure_debut__gt=timezone.now(),
                    statut_rdv__in=['PLANIFIE', 'CONFIRME']
                ).select_related('patient').order_by('date_heure_debut')[:10]
            }
            return render(request, 'gestion_rdv/dashboard_medecin.html', context)
        except Medecin.DoesNotExist:
            messages.error(request, "Profil médecin non trouvé.")
            return redirect('gestion_rdv:dashboard')
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="planning_dr_{medecin.utilisateur.nom_complet.replace(" ", "_")}.pdf"'
    
    # Dates
    date_debut = request.GET.get('date_debut')
    if date_debut:
        date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
    else:
        date_debut = date.today()
    
    date_fin = date_debut + timedelta(days=6)
    
    # Créer le PDF
    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Centré
    )
    
    story.append(Paragraph(f"Planning - Dr. {medecin.utilisateur.nom_complet}", title_style))
    story.append(Paragraph(f"Spécialité: {medecin.specialite}", styles['Normal']))
    story.append(Paragraph(f"Du {date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Récupérer les données
    rdv_queryset = RendezVous.objects.filter(
        medecin=medecin,
        date_heure_debut__date__range=[date_debut, date_fin],
        statut_rdv__in=['PLANIFIE', 'CONFIRME']
    ).select_related('patient').order_by('date_heure_debut')
    
    # Créer le tableau
    data = [['Date', 'Heure', 'Patient', 'Type', 'Durée', 'Notes']]
    
    for rdv in rdv_queryset:
        notes = rdv.notes_rdv[:30] + '...' if rdv.notes_rdv and len(rdv.notes_rdv) > 30 else rdv.notes_rdv or ''
        data.append([
            rdv.date_heure_debut.strftime('%d/%m/%Y'),
            rdv.date_heure_debut.strftime('%H:%M'),
            f"{rdv.patient.nom} {rdv.patient.prenom}",
            rdv.get_type_consultation_display(),
            f"{rdv.duree_minutes} min",
            notes
        ])
    
    if len(data) > 1:
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    else:
        story.append(Paragraph("Aucun rendez-vous trouvé pour cette période.", styles['Normal']))
    
    doc.build(story)
    return response


# ==================== RECHERCHE GLOBALE ====================

@login_required
def recherche_globale(request):
    """Recherche globale dans le système"""
    form = RechercheForm(request.GET or None)
    results = {
        'patients': [],
        'medecins': [],
        'rdv': []
    }
    
    if form.is_valid():
        query = form.cleaned_data['query']
        type_recherche = form.cleaned_data['type_recherche']
        
        if type_recherche in ['patient', 'tous']:
            results['patients'] = Patient.objects.filter(
                Q(nom__icontains=query) |
                Q(prenom__icontains=query) |
                Q(telephone__icontains=query) |
                Q(email__icontains=query)
            )[:10]
        
        if type_recherche in ['medecin', 'tous'] and request.user.role == 'SECRETAIRE':
            results['medecins'] = Medecin.objects.filter(
                Q(utilisateur__nom_complet__icontains=query) |
                Q(specialite__icontains=query) |
                Q(telephone_professionnel__icontains=query)
            ).select_related('utilisateur')[:10]
        
        if type_recherche in ['rdv', 'tous']:
            rdv_queryset = RendezVous.objects.filter(
                Q(patient__nom__icontains=query) |
                Q(patient__prenom__icontains=query) |
                Q(medecin__utilisateur__nom_complet__icontains=query) |
                Q(notes_rdv__icontains=query)
            ).select_related('patient', 'medecin__utilisateur')
            
            # Filtrer par médecin si c'est un médecin connecté
            if request.user.role == 'MEDECIN':
                try:
                    rdv_queryset = rdv_queryset.filter(medecin=request.user.medecin)
                except Medecin.DoesNotExist:
                    rdv_queryset = rdv_queryset.none()
            
            results['rdv'] = rdv_queryset[:10]
    
    context = {
        'form': form,
        'results': results,
        'query': form.cleaned_data.get('query', '') if form.is_valid() else ''
    }
    
    return render(request, 'gestion_rdv/recherche.html', context)Profil médecin non trouvé.")
            return redirect('login')
    
    else:
        messages.error(request, "Accès non autorisé.")
        return redirect('login')


# ==================== GESTION DES PATIENTS ====================

class PatientListView(SecretaireRequiredMixin, ListView):
    """Liste des patients"""
    model = Patient
    template_name = 'gestion_rdv/patients_list.html'
    context_object_name = 'patients'
    paginate_by = 20
    ordering = ['nom', 'prenom']

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(prenom__icontains=search) |
                Q(telephone__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        return context


class PatientDetailView(SecretaireRequiredMixin, DetailView):
    """Détail d'un patient"""
    model = Patient
    template_name = 'gestion_rdv/patient_detail.html'
    context_object_name = 'patient'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['rdv_list'] = self.object.rendezvous_set.select_related(
            'medecin__utilisateur'
        ).order_by('-date_heure_debut')
        return context


class PatientCreateView(SecretaireRequiredMixin, CreateView):
    """Création d'un patient"""
    model = Patient
    form_class = PatientForm
    template_name = 'gestion_rdv/patient_form.html'
    success_url = reverse_lazy('gestion_rdv:patients_list')

    def form_valid(self, form):
        messages.success(self.request, f"Patient {form.instance.get_identite()} créé avec succès.")
        return super().form_valid(form)


class PatientUpdateView(SecretaireRequiredMixin, UpdateView):
    """Modification d'un patient"""
    model = Patient
    form_class = PatientForm
    template_name = 'gestion_rdv/patient_form.html'
    success_url = reverse_lazy('gestion_rdv:patients_list')

    def form_valid(self, form):
        messages.success(self.request, f"Patient {form.instance.get_identite()} modifié avec succès.")
        return super().form_valid(form)


class PatientDeleteView(SecretaireRequiredMixin, DeleteView):
    """Suppression d'un patient"""
    model = Patient
    template_name = 'gestion_rdv/patient_confirm_delete.html'
    success_url = reverse_lazy('gestion_rdv:patients_list')

    def delete(self, request, *args, **kwargs):
        patient = self.get_object()
        messages.success(request, f"Patient {patient.get_identite()} supprimé avec succès.")
        return super().delete(request, *args, **kwargs)


@login_required
def patient_search(request):
    """Recherche AJAX de patients"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('q', '')
        if len(query) >= 2:
            patients = Patient.objects.filter(
                Q(nom__icontains=query) |
                Q(prenom__icontains=query) |
                Q(telephone__icontains=query)
            )[:10]
            
            results = [{
                'id': p.id,
                'text': f"{p.nom} {p.prenom} - {p.telephone}"
            } for p in patients]
            
            return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})


# ==================== GESTION DES MÉDECINS ====================

class MedecinListView(SecretaireRequiredMixin, ListView):
    """Liste des médecins"""
    model = Medecin
    template_name = 'gestion_rdv/medecins_list.html'
    context_object_name = 'medecins'
    ordering = ['utilisateur__nom_complet']

    def get_queryset(self):
        return super().get_queryset().select_related('utilisateur')


class MedecinDetailView(LoginRequiredMixin, DetailView):
    """Détail d'un médecin"""
    model = Medecin
    template_name = 'gestion_rdv/medecin_detail.html'
    context_object_name = 'medecin'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Prochains rendez-vous du médecin
        context['prochains_rdv'] = self.object.rendezvous_set.filter(
            date_heure_debut__gte=timezone.now(),
            statut_rdv__in=['PLANIFIE', 'CONFIRME']
        ).select_related('patient').order_by('date_heure_debut')[:10]
        return context


class MedecinCreateView(SecretaireRequiredMixin, CreateView):
    """Création d'un médecin"""
    model = Medecin
    form_class = MedecinForm
    template_name = 'gestion_rdv/medecin_form.html'
    success_url = reverse_lazy('gestion_rdv:medecins_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['user_form'] = MedecinUserForm(self.request.POST)
        else:
            context['user_form'] = MedecinUserForm()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context['user_form']
        
        if user_form.is_valid():
            user = user_form.save()
            form.instance.utilisateur = user
            messages.success(self.request, f"Médecin Dr. {user.nom_complet} créé avec succès.")
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class MedecinUpdateView(SecretaireRequiredMixin, UpdateView):
    """Modification d'un médecin"""
    model = Medecin
    form_class = MedecinForm
    template_name = 'gestion_rdv/medecin_form.html'
    success_url = reverse_lazy('gestion_rdv:medecins_list')

    def form_valid(self, form):
        messages.success(self.request, f"Médecin Dr. {form.instance.utilisateur.nom_complet} modifié avec succès.")
        return super().form_valid(form)


class MedecinDeleteView(SecretaireRequiredMixin, DeleteView):
    """Suppression d'un médecin"""
    model = Medecin
    template_name = 'gestion_rdv/medecin_confirm_delete.html'
    success_url = reverse_lazy('gestion_rdv:medecins_list')

    def delete(self, request, *args, **kwargs):
        medecin = self.get_object()
        messages.success(request, f"Médecin Dr. {medecin.utilisateur.nom_complet} supprimé avec succès.")
        return super().delete(request, *args, **kwargs)


# ==================== GESTION DES RENDEZ-VOUS ====================

class RendezVousListView(LoginRequiredMixin, ListView):
    """Liste des rendez-vous"""
    model = RendezVous
    template_name = 'gestion_rdv/rdv_list.html'
    context_object_name = 'rdv_list'
    paginate_by = 20
    ordering = ['-date_heure_debut']

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'patient', 'medecin__utilisateur', 'secretaire_creation'
        )
        
        # Filtrer par médecin si c'est un médecin connecté
        if self.request.user.role == 'MEDECIN':
            try:
                queryset = queryset.filter(medecin=self.request.user.medecin)
            except Medecin.DoesNotExist:
                queryset = queryset.none()
        
        # Filtres de recherche
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(patient__nom__icontains=search) |
                Q(patient__prenom__icontains=search) |
                Q(medecin__utilisateur__nom_complet__icontains=search)
            )
        
        statut = self.request.GET.get('statut')
        if statut:
            queryset = queryset.filter(statut_rdv=statut)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['statut_filter'] = self.request.GET.get('statut', '')
        context['statut_choices'] = RendezVous.STATUT_CHOICES
        return context


class RendezVousDetailView(LoginRequiredMixin, DetailView):
    """Détail d'un rendez-vous"""
    model = RendezVous
    template_name = 'gestion_rdv/rdv_detail.html'
    context_object_name = 'rdv'

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'patient', 'medecin__utilisateur', 'secretaire_creation'
        )
        
        # Filtrer par médecin si c'est un médecin connecté
        if self.request.user.role == 'MEDECIN':
            try:
                queryset = queryset.filter(medecin=self.request.user.medecin)
            except Medecin.DoesNotExist:
                queryset = queryset.none()
                
        return queryset


class RendezVousCreateView(SecretaireRequiredMixin, CreateView):
    """Création d'un rendez-vous"""
    model = RendezVous
    form_class = RendezVousForm
    template_name = 'gestion_rdv/rdv_form.html'
    success_url = reverse_lazy('gestion_rdv:rdv_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Rendez-vous créé avec succès.")
        return super().form_valid(form)


class RendezVousUpdateView(SecretaireRequiredMixin, UpdateView):
    """Modification d'un rendez-vous"""
    model = RendezVous
    form_class = RendezVousForm
    template_name = 'gestion_rdv/rdv_form.html'
    success_url = reverse_lazy('gestion_rdv:rdv_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, "Rendez-vous modifié avec succès.")
        return super().form_valid(form)


@login_required
def rdv_cancel(request, pk):
    """Annulation d'un rendez-vous"""
    rdv = get_object_or_404(RendezVous, pk=pk)
    
    # Vérifier les permissions
    if request.user.role != 'SECRETAIRE':
        messages.error(request, "Seules les secrétaires peuvent annuler un rendez-vous.")
        return redirect('gestion_rdv:rdv_detail', pk=pk)
    
    if request.method == 'POST':
        rdv.statut_rdv = 'ANNULE'
        rdv.save()
        messages.success(request, f"Rendez-vous de {rdv.patient} annulé avec succès.")
        return redirect('gestion_rdv:rdv_list')
    
    return render(request, 'gestion_rdv/rdv_confirm_cancel.html', {'rdv': rdv})


@login_required
def rdv_search(request):
    """Recherche de rendez-vous"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('q', '')
        if len(query) >= 2:
            rdv_list = RendezVous.objects.filter(
                Q(patient__nom__icontains=query) |
                Q(patient__prenom__icontains=query) |
                Q(medecin__utilisateur__nom_complet__icontains=query)
            ).select_related('patient', 'medecin__utilisateur')[:10]
            
            results = [{
                'id': rdv.id,
                'text': f"{rdv.patient} - Dr. {rdv.medecin.utilisateur.nom_complet} - {rdv.date_heure_debut.strftime('%d/%m/%Y %H:%M')}"
            } for rdv in rdv_list]
            
            return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})


# ==================== PLANNING ====================

@login_required
def planning_view(request):
    """Vue du planning général"""
    form = PlanningFilterForm(request.GET or None)
    
    # Dates par défaut
    date_debut = request.GET.get('date_debut')
    if date_debut:
        date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
    else:
        date_debut = date.today()
    
    date_fin = request.GET.get('date_fin')
    if date_fin:
        date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
    else:
        date_fin = date_debut + timedelta(days=6)  # Semaine par défaut
    
    # Filtrer les rendez-vous
    rdv_queryset = RendezVous.objects.filter(
        date_heure_debut__date__range=[date_debut, date_fin],
        statut_rdv__in=['PLANIFIE', 'CONFIRME']
    ).select_related('patient', 'medecin__utilisateur').order_by('date_heure_debut')
    
    # Filtrer par médecin si spécifié
    medecin_filter = request.GET.get('medecin')
    if medecin_filter:
        rdv_queryset = rdv_queryset.filter(medecin_id=medecin_filter)
    
    # Grouper par jour
    planning_data = {}
    current_date = date_debut
    while current_date <= date_fin:
        rdv_jour = rdv_queryset.filter(date_heure_debut__date=current_date)
        planning_data[current_date] = rdv_jour
        current_date += timedelta(days=1)
    
    context = {
        'form': form,
        'planning_data': planning_data,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }
    
    return render(request, 'gestion_rdv/planning.html', context)


@login_required
def planning_medecin(request, medecin_id):
    """Planning spécifique d'un médecin"""
    medecin = get_object_or_404(Medecin, pk=medecin_id)
    
    # Vérifier si c'est le médecin lui-même ou une secrétaire
    if request.user.role == 'MEDECIN':
        try:
            if request.user.medecin != medecin:
                messages.error(request, "Vous ne pouvez consulter que votre propre planning.")
                return redirect('gestion_rdv:dashboard')
        except Medecin.DoesNotExist:
            messages.error(request, "Profil médecin non trouvé.")
            return redirect('gestion_rdv:dashboard')
    
    # Dates par défaut
    date_debut = request.GET.get('date_debut')
    if date_debut:
        date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
    else:
        date_debut = date.today()
    
    date_fin = date_debut + timedelta(days=6)  # Semaine
    
    # Rendez-vous du médecin
    rdv_queryset = RendezVous.objects.filter(
        medecin=medecin,
        date_heure_debut__date__range=[date_debut, date_fin],
        statut_rdv__in=['PLANIFIE', 'CONFIRME']
    ).select_related('patient').order_by('date_heure_debut')
    
    # Grouper par jour
    planning_data = {}
    current_date = date_debut
    while current_date <= date_fin:
        rdv_jour = rdv_queryset.filter(date_heure_debut__date=current_date)
        planning_data[current_date] = rdv_jour
        current_date += timedelta(days=1)
    
    context = {
        'medecin': medecin,
        'planning_data': planning_data,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }
    
    return render(request, 'gestion_rdv/planning_medecin.html', context)


# ==================== AJAX ENDPOINTS ====================

@login_required
def get_creneaux_libres(request):
    """Retourne les créneaux libres pour un médecin à une date donnée"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        medecin_id = request.GET.get('medecin_id')
        date_str = request.GET.get('date')
        
        if medecin_id and date_str:
            try:
                medecin = Medecin.objects.get(pk=medecin_id)
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                # Récupérer les rendez-vous existants
                rdv_existants = RendezVous.objects.filter(
                    medecin=medecin,
                    date_heure_debut__date=date_obj,
                    statut_rdv__in=['PLANIFIE', 'CONFIRME']
                )
                
                # Générer les créneaux libres (exemple simplifié)
                creneaux_libres = []
                for heure in range(8, 18):  # 8h à 18h
                    for minute in [0, 30]:  # Créneaux de 30 minutes
                        heure_creneau = f"{heure:02d}:{minute:02d}"
                        datetime_creneau = datetime.combine(date_obj, datetime.strptime(heure_creneau, '%H:%M').time())
                        
                        # Vérifier si le créneau est libre
                        conflit = False
                        for rdv in rdv_existants:
                            if rdv.date_heure_debut <= datetime_creneau < rdv.date_heure_fin:
                                conflit = True
                                break
                        
                        if not conflit:
                            creneaux_libres.append({
                                'heure': heure_creneau,
                                'datetime': datetime_creneau.isoformat()
                            })
                
                return JsonResponse({'creneaux': creneaux_libres})
            
            except (Medecin.DoesNotExist, ValueError):
                pass
    
    return JsonResponse({'creneaux': []})


@login_required
def get_rdv_jour(request):
    """Retourne les rendez-vous d'une journée"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        date_str = request.GET.get('date')
        medecin_id = request.GET.get('medecin_id')
        
        if date_str:
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
                
                rdv_queryset = RendezVous.objects.filter(
                    date_heure_debut__date=date_obj,
                    statut_rdv__in=['PLANIFIE', 'CONFIRME']
                ).select_related('patient', 'medecin__utilisateur')
                
                if medecin_id:
                    rdv_queryset = rdv_queryset.filter(medecin_id=medecin_id)
                
                rdv_data = [{
                    'id': rdv.id,
                    'patient': f"{rdv.patient.nom} {rdv.patient.prenom}",
                    'medecin': rdv.medecin.utilisateur.nom_complet,
                    'heure': rdv.date_heure_debut.strftime('%H:%M'),
                    'duree': rdv.duree_minutes,
                    'type': rdv.get_type_consultation_display(),
                    'statut': rdv.get_statut_rdv_display()
                } for rdv in rdv_queryset]
                
                return JsonResponse({'rdv': rdv_data})
            
            except ValueError:
                pass
    
    return JsonResponse({'rdv': []})


# ==================== EXPORT PDF ====================

@login_required
def export_planning_pdf(request):
    """Export du planning général en PDF"""
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="planning_cabinet.pdf"'
    
    # Dates
    date_debut = request.GET.get('date_debut')
    if date_debut:
        date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
    else:
        date_debut = date.today()
    
    date_fin = date_debut + timedelta(days=6)
    
    # Créer le PDF
    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Titre
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Centré
    )
    
    story.append(Paragraph("Planning du Cabinet Médical", title_style))
    story.append(Paragraph(f"Du {date_debut.strftime('%d/%m/%Y')} au {date_fin.strftime('%d/%m/%Y')}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Récupérer les données
    rdv_queryset = RendezVous.objects.filter(
        date_heure_debut__date__range=[date_debut, date_fin],
        statut_rdv__in=['PLANIFIE', 'CONFIRME']
    ).select_related('patient', 'medecin__utilisateur').order_by('date_heure_debut')
    
    medecin_filter = request.GET.get('medecin')
    if medecin_filter:
        rdv_queryset = rdv_queryset.filter(medecin_id=medecin_filter)
    
    # Créer le tableau
    data = [['Date', 'Heure', 'Patient', 'Médecin', 'Type', 'Statut']]
    
    for rdv in rdv_queryset:
        data.append([
            rdv.date_heure_debut.strftime('%d/%m/%Y'),
            rdv.date_heure_debut.strftime('%H:%M'),
            f"{rdv.patient.nom} {rdv.patient.prenom}",
            f"Dr. {rdv.medecin.utilisateur.nom_complet}",
            rdv.get_type_consultation_display(),
            rdv.get_statut_rdv_display()
        ])
    
    if len(data) > 1:
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
    else:
        story.append(Paragraph("Aucun rendez-vous trouvé pour cette période.", styles['Normal']))
    
    doc.build(story)
    return response


@login_required
def export_planning_medecin_pdf(request, medecin_id):
    """Export du planning d'un médecin en PDF"""
    medecin = get_object_or_404(Medecin, pk=medecin_id)
    
    # Vérifier les permissions
    if request.user.role == 'MEDECIN':
        try:
            if request.user.medecin != medecin:
                messages.error(request, "Vous ne pouvez exporter que votre propre planning.")
                return redirect('gestion_rdv:planning_medecin', medecin_id=medecin_id)
        except Medecin.DoesNotExist:
            messages.error(request, "Profil médecin non trouvé.")
            return redirect('gestion_rdv:planning_medecin', medecin_id=medecin_id)
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="planning_dr_{medecin.utilisateur.nom_complet.replace(" ", "_")}.pdf"'
    