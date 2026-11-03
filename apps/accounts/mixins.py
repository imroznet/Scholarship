from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied


class RoleGateMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Send anonymous visitors to login and deny signed-in users without the role."""

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return LoginRequiredMixin.handle_no_permission(self)
        raise PermissionDenied


class SuperAdminRequiredMixin(RoleGateMixin):
    def test_func(self):
        return self.request.user.is_super_admin


class StaffRequiredMixin(RoleGateMixin):
    def test_func(self):
        user = self.request.user
        return user.is_super_admin or user.is_operator
