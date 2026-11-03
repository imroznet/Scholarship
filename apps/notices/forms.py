from django import forms

from apps.core.forms import BanglaFormMixin
from apps.notices.models import Notice
from apps.sessions.models import ScholarshipSession


class NoticeForm(BanglaFormMixin, forms.ModelForm):
    class Meta:
        model = Notice
        fields = [
            "scholarship_session",
            "title_bn",
            "slug",
            "content_bn",
            "published_at",
            "expires_at",
            "is_featured",
            "status",
        ]
        labels = {
            "scholarship_session": "সেশন",
            "title_bn": "শিরোনাম",
            "slug": "স্লাগ",
            "content_bn": "বিবরণ",
            "published_at": "প্রকাশের সময়",
            "expires_at": "মেয়াদ শেষ",
            "is_featured": "গুরুত্বপূর্ণ",
            "status": "অবস্থা",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["scholarship_session"].queryset = ScholarshipSession.objects.order_by("-start_date")
        self.fields["slug"].required = False

    def clean(self):
        cleaned = super().clean()
        published = cleaned.get("published_at")
        expires = cleaned.get("expires_at")
        if published and expires and expires <= published:
            self.add_error("expires_at", "মেয়াদ শেষের সময় প্রকাশের সময়ের পরে হতে হবে।")
        return cleaned
