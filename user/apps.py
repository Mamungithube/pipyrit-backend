from django.apps import AppConfig


class UserConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user'

    def ready(self):
        # এই লাইনটি সিগন্যালকে সচল করবে
        import user.signals