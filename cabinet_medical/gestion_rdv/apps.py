from django.apps import AppConfig


class GestionRdvConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gestion_rdv'
    verbose_name = 'Gestion des Rendez-vous'
    
    def ready(self):
        """
        Code exécuté quand l'application est prête
        """
        # Import des signaux si nécessaire
        # import gestion_rdv.signals
        pass