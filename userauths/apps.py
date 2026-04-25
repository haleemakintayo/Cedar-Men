from django.apps import AppConfig


class UserauthsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'userauths'

    def ready(self):
        from Cedarmen.unfold_compat import patch_unfold_flatten_context

        patch_unfold_flatten_context()
