from django.apps import AppConfig


class RegistryConfig(AppConfig):
    name = "config"
    label = "service_registry"

    def ready(self):
        from .consul import start_registration
        start_registration()
