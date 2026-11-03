import os
import re
import uuid
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

Image.MAX_IMAGE_PIXELS = 20_000_000

ALLOWED_FORMATS = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}
ALLOWED_CONTENT_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}
SAFE_NAME = re.compile(r"[^A-Za-z0-9._\-\u0980-\u09FF ]+")


def _read_image(uploaded, max_bytes):
    if uploaded is None:
        raise ValidationError("ফাইল নির্বাচন করুন।")
    size = getattr(uploaded, "size", None)
    if size is not None and size > max_bytes:
        raise ValidationError(f"ফাইলের আকার সর্বোচ্চ {max(1, max_bytes // (1024 * 1024))} এমবি।")
    name = (getattr(uploaded, "name", "") or "").lower()
    content_type = (getattr(uploaded, "content_type", "") or "").lower()
    if name.endswith(".svg") or "svg" in content_type:
        raise ValidationError("SVG ফাইল গ্রহণ করা হয় না। PNG, JPG বা WebP ব্যবহার করুন।")
    if content_type and content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError("শুধু PNG, JPG, JPEG বা WebP ছবি আপলোড করা যাবে।")
    raw = uploaded.read()
    if len(raw) > max_bytes:
        raise ValidationError(f"ফাইলের আকার সর্বোচ্চ {max(1, max_bytes // (1024 * 1024))} এমবি।")
    if raw.lstrip()[:1] == b"<" or b"<svg" in raw[:800].lower():
        raise ValidationError("SVG ফাইল গ্রহণ করা হয় না।")
    try:
        probe = Image.open(BytesIO(raw))
        probe.verify()
        image = Image.open(BytesIO(raw))
        image.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValidationError("ছবির বিষয়বস্তু যাচাই করা যায়নি।") from exc
    fmt = (image.format or "").upper()
    if fmt not in ALLOWED_FORMATS:
        raise ValidationError("ছবির ধরন সমর্থিত নয়।")
    if image.width < 32 or image.height < 32:
        raise ValidationError("ছবি কমপক্ষে ৩২ পিক্সেল হতে হবে।")
    if image.width > 8000 or image.height > 8000:
        raise ValidationError("ছবির মাত্রা খুব বড়।")
    if hasattr(uploaded, "seek"):
        uploaded.seek(0)
    return raw, image, fmt


def process_image(uploaded, *, max_bytes, max_px, keep_original=False):
    raw, image, fmt = _read_image(uploaded, max_bytes)
    image = ImageOps.exif_transpose(image)
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")
    has_alpha = False
    if image.mode == "RGBA":
        low, _high = image.getchannel("A").getextrema()
        has_alpha = low < 255
    display = image.copy()
    display.thumbnail((max_px, max_px), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    if has_alpha:
        if display.mode != "RGBA":
            display = display.convert("RGBA")
        display.save(buffer, format="PNG", optimize=True)
        extension = ".png"
    else:
        display = display.convert("RGB")
        display.save(buffer, format="JPEG", quality=85, optimize=True)
        extension = ".jpg"
    display_file = ContentFile(buffer.getvalue(), name=f"{uuid.uuid4().hex}{extension}")
    original_file = None
    if keep_original:
        original_file = ContentFile(raw, name=f"{uuid.uuid4().hex}{ALLOWED_FORMATS[fmt]}")
    return display_file, original_file


def process_attachment(uploaded, *, max_bytes):
    if uploaded is None:
        raise ValidationError("সংযুক্তি নির্বাচন করুন।")
    if uploaded.size > max_bytes:
        raise ValidationError(f"সংযুক্তি সর্বোচ্চ {max(1, max_bytes // (1024 * 1024))} এমবি।")
    original = os.path.basename(uploaded.name or "attachment")
    original = SAFE_NAME.sub("_", original).strip("._ ")[:80] or "attachment"
    ext = os.path.splitext(original)[1].lower()
    raw = uploaded.read()
    if len(raw) > max_bytes:
        raise ValidationError("সংযুক্তি অনুমোদিত আকারের চেয়ে বড়।")
    if ext == ".pdf":
        if not raw.startswith(b"%PDF"):
            raise ValidationError("সঠিক PDF ফাইল নয়।")
        stored = ContentFile(raw, name=f"{uuid.uuid4().hex}.pdf")
        return stored, original
    if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise ValidationError("সংযুক্তি শুধু PDF, PNG, JPG বা WebP হতে পারবে।")
    display, _original = process_image(uploaded_from_raw(raw, original), max_bytes=max_bytes, max_px=1600)
    return display, original


class _MemoryUpload:
    def __init__(self, raw, name):
        self._raw = raw
        self.name = name
        self.size = len(raw)
        self.content_type = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".webp": "image/webp",
        }.get(os.path.splitext(name)[1].lower(), "image/jpeg")
        self._buffer = BytesIO(raw)

    def read(self):
        return self._buffer.read()

    def seek(self, pos):
        self._buffer.seek(pos)


def uploaded_from_raw(raw, name):
    return _MemoryUpload(raw, name)


def content_type_for(name):
    ext = os.path.splitext(name or "")[1].lower()
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".pdf": "application/pdf",
    }.get(ext, "application/octet-stream")
