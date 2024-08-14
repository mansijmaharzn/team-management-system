from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "This is a description of what my_command does"

    def add_arguments(self, parser):
        # nargs='?' specified arg is optional
        parser.add_argument(
            "sample_arg", nargs="?", default="", type=str, help="A sample argument"
        )

    def handle(self, *args, **kwargs):
        sample_arg = kwargs["sample_arg"]
        if sample_arg:
            self.stdout.write(f"Thikcha, {sample_arg}")
        else:
            self.stdout.write("Thikcha")
