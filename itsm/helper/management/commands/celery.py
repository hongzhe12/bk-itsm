import atexit
import subprocess
import sys

from celery.bin.celery import celery as celery_cli
from click.exceptions import Exit
from django.conf import settings
from django.core.management.base import BaseCommand


def split_worker_beat_args(args):
    if not args or args[0] != "worker" or not ({"-B", "--beat"} & set(args)):
        return args, None

    worker_args = [arg for arg in args if arg not in {"-B", "--beat"}]
    if settings.STANDALONE_MODE and not ({"-P", "--pool"} & set(worker_args)):
        worker_args += ["--pool", "solo"]
    loglevel = worker_args[worker_args.index("-l") + 1] if "-l" in worker_args else "info"
    return worker_args, [
        "beat",
        "-l",
        loglevel,
        "--scheduler",
        "django_celery_beat.schedulers:DatabaseScheduler",
    ]


class Command(BaseCommand):
    help = "Run Celery, with standalone-compatible embedded beat"

    def run_from_argv(self, argv):
        worker_args, beat_args = split_worker_beat_args(argv[2:])
        beat_process = None

        def stop_beat():
            if beat_process and beat_process.poll() is None:
                beat_process.terminate()
                beat_process.wait()

        if beat_args:
            beat_process = subprocess.Popen(
                [sys.executable, "manage.py", "celery", *beat_args]
            )
            atexit.register(stop_beat)

        try:
            celery_cli.main(args=worker_args, standalone_mode=False)
        except Exit as error:
            self.stdout.write(f"celery command error: {error}")
            return error.exit_code
        finally:
            stop_beat()
