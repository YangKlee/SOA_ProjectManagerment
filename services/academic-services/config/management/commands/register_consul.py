from django.core.management.base import BaseCommand, CommandError
from config.consul import RegistrationError, register


class Command(BaseCommand):
    help = "Register or deregister this service in Consul."

    def add_arguments(self, parser):
        parser.add_argument("--deregister", action="store_true")

    def handle(self, *args, **options):
        try:
            register(deregister=options["deregister"])
        except RegistrationError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS("Service registry updated."))
