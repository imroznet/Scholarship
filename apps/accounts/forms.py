from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from apps.core.forms import BanglaFormMixin


class StyledAuthenticationForm(BanglaFormMixin, AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "ব্যবহারকারী নাম"
        self.fields["password"].label = "পাসওয়ার্ড"


class StyledPasswordChangeForm(BanglaFormMixin, PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["old_password"].label = "বর্তমান পাসওয়ার্ড"
        self.fields["new_password1"].label = "নতুন পাসওয়ার্ড"
        self.fields["new_password2"].label = "নতুন পাসওয়ার্ড নিশ্চিত করুন"


class OperatorForm(BanglaFormMixin, forms.Form):
    username = forms.CharField(label="ব্যবহারকারী নাম", max_length=150)
    first_name = forms.CharField(label="নাম", max_length=150)
    last_name = forms.CharField(label="পদবি", max_length=150, required=False)
    email = forms.EmailField(label="ইমেইল", required=False)
    phone = forms.CharField(label="ফোন", max_length=20, required=False)
    password1 = forms.CharField(label="পাসওয়ার্ড", required=False, widget=forms.PasswordInput)
    password2 = forms.CharField(label="পাসওয়ার্ড নিশ্চিত করুন", required=False, widget=forms.PasswordInput)
    is_active = forms.BooleanField(label="সক্রিয়", required=False, initial=True)

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        super().__init__(*args, **kwargs)
        if instance is not None:
            self.fields["username"].disabled = True
            self.fields["password1"].help_text = "খালি রাখলে পাসওয়ার্ড পরিবর্তন হবে না।"
        else:
            self.fields["password1"].required = True
            self.fields["password2"].required = True

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        queryset = User.objects.filter(username__iexact=username)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError("এই ব্যবহারকারী নাম আগে থেকে আছে।")
        return username

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password1") or ""
        confirm = cleaned.get("password2") or ""
        if password or confirm or self.instance is None:
            if password != confirm:
                self.add_error("password2", "পাসওয়ার্ড মিলছে না।")
            if password:
                try:
                    validate_password(password, self.instance)
                except ValidationError as exc:
                    self.add_error("password1", exc)
        return cleaned

    def save(self):
        if self.instance is None:
            user = User(
                username=self.cleaned_data["username"],
                role=User.Role.DATA_ENTRY_OPERATOR,
            )
        else:
            user = self.instance
            user.role = User.Role.DATA_ENTRY_OPERATOR
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = (self.cleaned_data.get("last_name") or "").strip()
        user.email = self.cleaned_data.get("email") or ""
        user.phone = (self.cleaned_data.get("phone") or "").strip()
        user.is_active = bool(self.cleaned_data.get("is_active"))
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        user.save()
        return user
