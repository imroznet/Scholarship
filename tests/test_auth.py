from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from tests.helpers import ScholarshipTestCase


class AuthenticationTests(ScholarshipTestCase):
    def test_super_admin_login(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "admin", "password": self.password},
        )
        self.assertRedirects(response, reverse("dashboard:home"))
        page = self.client.get(reverse("dashboard:home"))
        self.assertContains(page, "মোট শিক্ষার্থী")
        self.assertContains(page, "ড্যাশবোর্ড")

    def test_operator_login_and_limited_navigation(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": "operator", "password": self.password},
        )
        self.assertRedirects(response, reverse("dashboard:home"))
        page = self.client.get(reverse("dashboard:home"))
        self.assertContains(page, "শিক্ষার্থী ব্যবস্থাপনা")
        self.assertNotContains(page, "ব্র্যান্ডিং")

    def test_anonymous_dashboard_redirects_to_login(self):
        response = self.client.get(reverse("dashboard:home"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('dashboard:home')}")

    def test_operator_cannot_open_super_admin_modules(self):
        self.login("operator")
        for url in (
            reverse("branding:manage"),
            reverse("sessions:list"),
            reverse("institutes:list"),
            reverse("academics:classes"),
            reverse("verification:list"),
            reverse("schedules:list"),
            reverse("results:home"),
            reverse("winners:list"),
            reverse("users:list"),
            reverse("audit:list"),
            reverse("settings:manage"),
        ):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403, url)

    def test_role_flags_follow_the_role_field(self):
        self.operator.is_superuser = True
        self.operator.is_staff = True
        self.operator.save()
        self.operator.refresh_from_db()
        self.assertFalse(self.operator.is_superuser)
        self.assertTrue(self.operator.is_operator)
        self.admin.role = User.Role.DATA_ENTRY_OPERATOR
        self.admin.save()
        self.admin.refresh_from_db()
        self.assertFalse(self.admin.is_super_admin)

    def test_repeated_login_failures_are_throttled(self):
        url = reverse("accounts:login")
        for _ in range(5):
            response = self.client.post(url, {"username": "admin", "password": "wrong-password"})
            self.assertEqual(response.status_code, 200)
        locked = self.client.post(url, {"username": "admin", "password": self.password})
        self.assertEqual(locked.status_code, 200)
        self.assertContains(locked, "অনেকবার ভুল চেষ্টা")

    def test_inactive_user_is_logged_out(self):
        self.login("operator")
        self.operator.is_active = False
        self.operator.save(update_fields=["is_active"])
        response = self.client.get(reverse("students:list"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('students:list')}")


class PermissionFlagTests(TestCase):
    def test_create_user_defaults_to_operator(self):
        user = User.objects.create_user("clerk", password="Scholar-Admin-2026!")
        self.assertEqual(user.role, User.Role.DATA_ENTRY_OPERATOR)
        self.assertFalse(user.is_superuser)
