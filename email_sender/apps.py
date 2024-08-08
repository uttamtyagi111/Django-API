from django.apps import AppConfig

class EmailSenderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'email_sender'

    def ready(self):
        # Perform startup tasks here, if any
        pass
