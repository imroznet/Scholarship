import os
from datetime import date

from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.branding.defaults import DEFAULT_SHORT_NAME, DEFAULT_SPONSOR_NAME_BN, DEFAULT_SPONSOR_NAME_EN
from apps.institutes.models import Category
from apps.sessions.models import ScholarshipSession
from apps.sessions.services import set_active_session


class Command(BaseCommand):
    help = "Create the initial categories and the 2026 scholarship session if they are missing."

    def handle(self, *args, **options):
        categories = [
            ("সাধারণ", "General", "general"),
            ("মাদ্রাসা", "Madrasa", "madrasa"),
        ]
        for name_bn, name_en, code in categories:
            category, created = Category.objects.get_or_create(
                code=code,
                defaults={"name_bn": name_bn, "name_en": name_en, "is_active": True},
            )
            self.stdout.write(f"category {category.code} {'created' if created else 'exists'}")

        session, created = ScholarshipSession.objects.get_or_create(
            code="26",
            defaults={
                "name_bn": "কান্ট্রি গ্রুপ স্কলারশিপ - ২০২৬",
                "name_en": "Country Group Scholarship - 2026",
                "start_date": date(2026, 1, 1),
                "end_date": date(2026, 12, 31),
                "is_active": False,
                "description": "",
            },
        )
        if not ScholarshipSession.objects.filter(is_active=True).exists():
            set_active_session(session)
        branding = session.branding
        if created or not branding.sponsor_name_bn:
            branding.name_bn = "কান্ট্রি গ্রুপ স্কলারশিপ - ২০২৬"
            branding.name_en = "Country Group Scholarship - 2026"
            branding.short_name = DEFAULT_SHORT_NAME
            branding.sponsor_name_bn = DEFAULT_SPONSOR_NAME_BN
            branding.sponsor_name_en = DEFAULT_SPONSOR_NAME_EN
            branding.save()
        self.stdout.write(f"session {session.code} {'created' if created else 'exists'}")

        username = os.environ.get("BOOTSTRAP_ADMIN_USERNAME", "").strip()
        password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD", "")
        if username and password and not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username,
                email=os.environ.get("BOOTSTRAP_ADMIN_EMAIL", ""),
                password=password,
            )
            self.stdout.write(f"super admin {username} created")
        elif not User.objects.filter(role=User.Role.SUPER_ADMIN).exists():
            self.stdout.write("No super admin yet. Run: python manage.py createsuperuser")
