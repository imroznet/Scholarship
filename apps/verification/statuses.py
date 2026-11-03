from django.db import models


class VerificationStatus(models.TextChoices):
    PENDING = "PENDING", "অপেক্ষমাণ"
    VERIFIED = "VERIFIED", "যাচাইকৃত"
    REJECTED = "REJECTED", "বাতিল"
    CORRECTION_REQUIRED = "CORRECTION_REQUIRED", "সংশোধন প্রয়োজন"
