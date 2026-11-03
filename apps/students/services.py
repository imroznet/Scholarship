import os
import time
import uuid

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import IntegrityError, OperationalError, connection, transaction
from django.utils import timezone

from apps.academics.models import ClassRegistrationSetting
from apps.audit.services import log_action
from apps.sessions.models import ScholarshipSession
from apps.students.models import Student, StudentSequence
from apps.verification.models import VerificationHistory
from apps.verification.statuses import VerificationStatus

PHOTO_KEY = "pending_student_photo"


def ensure_class_open(session, academic_class, at=None):
    setting = (
        ClassRegistrationSetting.objects.filter(
            scholarship_session=session,
            academic_class=academic_class,
        )
        .select_related("academic_class")
        .first()
    )
    if setting is None or not setting.is_currently_open(at):
        raise ValidationError("এই শ্রেণির নিবন্ধন এখন বন্ধ।")


def increment_sequence_field(sequence_pk, field_name):
    """Return the next counter value inside the caller's transaction.

    PostgreSQL and MySQL lock the sequence row. SQLite has no row locks, so the
    increment uses a single UPDATE ... RETURNING statement, which SQLite
    serializes with its database write lock.
    """
    if field_name not in {"last_number", "certificate_last_number"}:
        raise ValueError(field_name)
    field = StudentSequence._meta.get_field(field_name)
    if connection.vendor == "sqlite":
        table = connection.ops.quote_name(StudentSequence._meta.db_table)
        column = connection.ops.quote_name(field.column)
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE {table} SET {column} = {column} + 1 WHERE id = %s RETURNING {column}",
                [sequence_pk],
            )
            row = cursor.fetchone()
        if row is None:
            raise ValidationError("সিকোয়েন্স পাওয়া যায়নি।")
        return row[0]
    locked = StudentSequence.objects.select_for_update().get(pk=sequence_pk)
    value = getattr(locked, field_name) + 1
    setattr(locked, field_name, value)
    locked.save(update_fields=[field_name, "updated_at"])
    return value


def allocate_student_id(session):
    if transaction.get_connection().in_atomic_block:
        return _allocate_student_id(session)
    with transaction.atomic():
        return _allocate_student_id(session)


def _allocate_student_id(session):
    session = ScholarshipSession.objects.select_for_update().get(pk=session.pk)
    branding = getattr(session, "branding", None)
    short_name = branding.short_name if branding else "ID"
    sequence, _created = StudentSequence.objects.get_or_create(
        scholarship_session=session,
        defaults={"prefix": f"{short_name}{session.code}", "last_number": 0, "certificate_last_number": 0},
    )
    number = increment_sequence_field(sequence.pk, "last_number")
    sequence.refresh_from_db(fields=["prefix"])
    return f"{sequence.prefix}-{number:04d}"


def find_duplicate_warnings(*, name_bn, name_en, date_of_birth, mobile, father_mobile, institute, exclude_pk=None):
    queryset = Student.objects.alive()
    if exclude_pk:
        queryset = queryset.exclude(pk=exclude_pk)
    warnings = []
    if queryset.filter(name_bn=name_bn, date_of_birth=date_of_birth).exists():
        warnings.append("একই নাম ও জন্ম তারিখের শিক্ষার্থী আগে থেকে আছে।")
    if mobile and queryset.filter(mobile=mobile).exists():
        warnings.append("একই মোবাইল নম্বর অন্য শিক্ষার্থীর সাথে মিলেছে।")
    if name_en and institute is not None and queryset.filter(name_en__iexact=name_en, institute=institute).exists():
        warnings.append("একই ইংরেজি নাম ও প্রতিষ্ঠানের শিক্ষার্থী আগে থেকে আছে।")
    if father_mobile and name_bn and queryset.filter(father_mobile=father_mobile, name_bn=name_bn).exists():
        warnings.append("একই অভিভাবকের মোবাইল ও শিক্ষার্থীর নামের মিল পাওয়া গেছে।")
    elif father_mobile and queryset.filter(father_mobile=father_mobile).exists():
        warnings.append("অভিভাবকের মোবাইল নম্বর অন্য শিক্ষার্থীর সাথে মিলেছে। এটি স্বয়ংক্রিয়ভাবে বাতিল করা হয়নি।")
    return warnings


def _snapshot(student):
    return {
        "name_bn": student.name_bn,
        "name_en": student.name_en,
        "mobile": student.mobile,
        "institute_id": student.institute_id,
        "academic_class_id": student.academic_class_id,
        "category_id": student.category_id,
        "verification_status": student.verification_status,
        "is_active": student.is_active,
    }


def register_student(*, actor, photo, cleaned, request=None):
    last_error = None
    for attempt in range(5):
        try:
            with transaction.atomic():
                return _register_student(actor=actor, photo=photo, cleaned=cleaned, request=request)
        except (OperationalError, IntegrityError) as exc:
            last_error = exc
            time.sleep(0.05 * (attempt + 1))
    raise last_error


def _register_student(*, actor, photo, cleaned, request):
    from apps.sessions.selectors import get_active_session

    if hasattr(photo, "seek"):
        photo.seek(0)
    session = get_active_session()
    if session is None:
        raise ValidationError("কোনো সক্রিয় স্কলারশিপ সেশন নেই।")
    session = ScholarshipSession.objects.select_for_update().get(pk=session.pk)
    institute = cleaned["institute"]
    if not institute.is_active:
        raise ValidationError("নিষ্ক্রিয় প্রতিষ্ঠান নির্বাচন করা যাবে না।")
    academic_class = cleaned["academic_class"]
    ensure_class_open(session, academic_class)
    student = Student(
        scholarship_session=session,
        student_id=allocate_student_id(session),
        name_bn=cleaned["name_bn"].strip(),
        name_en=cleaned["name_en"].strip(),
        date_of_birth=cleaned["date_of_birth"],
        mobile=cleaned["mobile"].strip(),
        father_name=(cleaned.get("father_name") or "").strip(),
        father_mobile=(cleaned.get("father_mobile") or "").strip(),
        mother_name=(cleaned.get("mother_name") or "").strip(),
        mother_mobile=(cleaned.get("mother_mobile") or "").strip(),
        village=cleaned["village"].strip(),
        post_office=cleaned["post_office"].strip(),
        upazila=cleaned["upazila"].strip(),
        district=cleaned["district"].strip(),
        institute=institute,
        category=institute.category,
        category_name_bn=institute.category.name_bn,
        academic_class=academic_class,
        verification_status=VerificationStatus.PENDING,
        registered_by=actor,
        is_active=True,
    )
    student.photo.save(photo.name, photo, save=False)
    student.full_clean()
    student.save()
    VerificationHistory.objects.create(
        student=student,
        status=VerificationStatus.PENDING,
        remarks="নিবন্ধন তৈরি হয়েছে।",
        verified_by=actor,
        verified_at=timezone.now(),
    )
    log_action(request=request, action="student.create", instance=student, changes=_snapshot(student))
    return student


def update_student(*, student, actor, cleaned, photo=None, request=None):
    with transaction.atomic():
        student = Student.objects.select_for_update().select_related("institute", "academic_class").get(pk=student.pk)
        if student.deleted_at:
            raise ValidationError("মুছে ফেলা রেকর্ড সম্পাদনা করা যাবে না।")
        before = _snapshot(student)
        institute = cleaned["institute"]
        academic_class = cleaned["academic_class"]
        if academic_class.pk != student.academic_class_id:
            if actor.is_super_admin:
                if not academic_class.is_active:
                    raise ValidationError("নিষ্ক্রিয় শ্রেণি নির্বাচন করা যাবে না।")
            else:
                ensure_class_open(student.scholarship_session, academic_class)
        if institute.pk != student.institute_id and not institute.is_active:
            raise ValidationError("নিষ্ক্রিয় প্রতিষ্ঠান নির্বাচন করা যাবে না।")
        student.name_bn = cleaned["name_bn"].strip()
        student.name_en = cleaned["name_en"].strip()
        student.date_of_birth = cleaned["date_of_birth"]
        student.mobile = cleaned["mobile"].strip()
        student.father_name = (cleaned.get("father_name") or "").strip()
        student.father_mobile = (cleaned.get("father_mobile") or "").strip()
        student.mother_name = (cleaned.get("mother_name") or "").strip()
        student.mother_mobile = (cleaned.get("mother_mobile") or "").strip()
        student.village = cleaned["village"].strip()
        student.post_office = cleaned["post_office"].strip()
        student.upazila = cleaned["upazila"].strip()
        student.district = cleaned["district"].strip()
        student.academic_class = academic_class
        if institute.pk != student.institute_id:
            student.institute = institute
            student.category = institute.category
            student.category_name_bn = institute.category.name_bn
        old_photo = ""
        if photo is not None:
            old_photo = student.photo.name
            student.photo.save(photo.name, photo, save=False)
        if actor.is_super_admin and "is_active" in cleaned:
            student.is_active = bool(cleaned["is_active"])
        student.full_clean()
        student.save()
        if old_photo and old_photo != student.photo.name:
            default_storage.delete(old_photo)
        log_action(
            request=request,
            action="student.update",
            instance=student,
            changes={"from": before, "to": _snapshot(student)},
        )
        return student


def soft_delete_student(*, student, actor, request=None):
    with transaction.atomic():
        student = Student.objects.select_for_update().get(pk=student.pk)
        if student.deleted_at:
            return student
        student.soft_delete()
        log_action(request=request, action="student.soft_delete", instance=student)
        return student


def restore_student(*, student, actor, request=None):
    with transaction.atomic():
        student = Student.objects.select_for_update().get(pk=student.pk)
        student.deleted_at = None
        student.is_active = True
        student.save(update_fields=["deleted_at", "is_active", "updated_at"])
        log_action(request=request, action="student.restore", instance=student)
        return student


def stash_processed_image(request, content, key=PHOTO_KEY):
    clear_stashed_image(request, key)
    suffix = os.path.splitext(content.name)[1].lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        suffix = ".jpg"
    path = default_storage.save(f"private/tmp/{uuid.uuid4().hex}{suffix}", content)
    request.session[key] = path
    request.session.modified = True
    return path


def stashed_image_path(request, key=PHOTO_KEY):
    path = request.session.get(key) or ""
    if not path.startswith("private/tmp/") or ".." in path:
        return ""
    if not default_storage.exists(path):
        return ""
    return path


def read_stashed_image(path):
    with default_storage.open(path, "rb") as handle:
        data = handle.read()
    return ContentFile(data, name=os.path.basename(path))


def clear_stashed_image(request, key=PHOTO_KEY):
    path = request.session.pop(key, "") or ""
    request.session.modified = True
    if path.startswith("private/tmp/") and ".." not in path and default_storage.exists(path):
        default_storage.delete(path)
