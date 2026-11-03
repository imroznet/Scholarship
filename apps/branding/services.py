from django.core.files.storage import default_storage

from apps.branding.defaults import reset_branding_values
from apps.core.uploads import process_image

IMAGE_FIELDS = (
    ("logo", "logo_original", 800, True),
    ("sponsor_logo", "sponsor_logo_original", 800, True),
    ("favicon", "", 128, False),
    ("secondary_logo", "secondary_logo_original", 800, True),
    ("signature_image", "", 700, False),
    ("seal_image", "", 700, False),
)


def _delete_field(instance, field_name):
    if not field_name:
        return
    current = getattr(instance, field_name)
    name = current.name if current else ""
    if name:
        current.delete(save=False)
        if default_storage.exists(name):
            default_storage.delete(name)


def apply_brand_images(branding, files, *, max_bytes, clear_fields=()):
    prepared = {}
    for field_name, original_name, max_px, keep_original in IMAGE_FIELDS:
        upload = files.get(field_name)
        if upload:
            prepared[field_name] = (
                original_name,
                process_image(upload, max_bytes=max_bytes, max_px=max_px, keep_original=keep_original),
            )
    for field_name, original_name, _max_px, _keep in IMAGE_FIELDS:
        if field_name in clear_fields or field_name in prepared:
            _delete_field(branding, field_name)
            _delete_field(branding, original_name)
        if field_name not in prepared:
            continue
        original_field, (display, original) = prepared[field_name]
        getattr(branding, field_name).save(display.name, display, save=False)
        if original_field and original is not None:
            getattr(branding, original_field).save(original.name, original, save=False)
    branding.save()
    return branding


def reset_branding(branding):
    from apps.students.models import StudentSequence

    values = reset_branding_values(branding.session)
    sequence = StudentSequence.objects.filter(scholarship_session_id=branding.session_id).first()
    if sequence and (sequence.last_number or sequence.certificate_last_number):
        values["short_name"] = branding.short_name
    for field, value in values.items():
        setattr(branding, field, value)
    for field_name, original_name, _max_px, _keep in IMAGE_FIELDS:
        _delete_field(branding, field_name)
        _delete_field(branding, original_name)
    branding.save()
    return branding
