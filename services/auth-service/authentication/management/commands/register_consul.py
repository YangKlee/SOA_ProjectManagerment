from django.core.management.base import BaseCommand, CommandError

from authentication.consul import (
    ConsulRegistrationError,
    deregister_auth_service,
    register_auth_service,
)


class Command(BaseCommand):
    help = "Register or deregister auth-service in Consul."

    def add_arguments(self, parser):
        parser.add_argument(
            "--deregister",
            action="store_true",
            help="Remove this auth-service instance from Consul.",
        )

    def handle(self, *args, **options):
        try:
            if options["deregister"]:
                deregister_auth_service()
                self.stdout.write(self.style.SUCCESS("Auth service deregistered from Consul."))
            else:
                register_auth_service()
                self.stdout.write(self.style.SUCCESS("Auth service registered with Consul."))
        except ConsulRegistrationError as exc:
            raise CommandError(str(exc)) from exc
