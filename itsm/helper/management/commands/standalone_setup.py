import os

from blueapps.account.models import User, UserProperty
from django.conf import settings
from django.core.management.base import BaseCommand

from itsm.iadmin.models import SystemSettings


class Command(BaseCommand):
    help = "Initialize local BK-ITSM administrator and standalone settings"

    def handle(self, *args, **options):
        username = os.getenv("STANDALONE_ADMIN_USERNAME", "admin")
        user, _ = User.objects.get_or_create(username=username)
        user.nickname = os.getenv("STANDALONE_ADMIN_DISPLAY_NAME", username)
        user.is_staff = True
        user.is_active = True
        user.is_superuser = True
        user.set_password(os.getenv("STANDALONE_ADMIN_PASSWORD", "admin"))
        user.save()
        UserProperty.objects.update_or_create(
            user=user,
            key="chname",
            defaults={"value": user.nickname},
        )

        file_root = os.path.join(settings.PROJECT_ROOT, "USERRES")
        os.makedirs(file_root, exist_ok=True)
        settings_values = {
            "SYS_FILE_PATH": file_root,
            "IS_ORGANIZATION": "off",
            "NOTICE_CENTER_SWITCH": "off",
            "SERVICE_SWITCH": "on",
        }
        for key, value in settings_values.items():
            setting, _ = SystemSettings.objects.get_or_create(
                key=key,
                defaults={"type": "FUNCTION", "creator": "system", "updated_by": "system"},
            )
            setting.value = value
            setting.save(update_fields=["value", "update_at"])

        self.stdout.write(
            self.style.SUCCESS(
                f"Standalone initialization completed for user {username}"
            )
        )
