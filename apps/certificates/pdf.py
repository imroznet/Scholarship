import os
from io import BytesIO

from django.conf import settings
from django.utils import timezone
from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from apps.branding.defaults import DEFAULT_CERTIFICATE_FOOTER, DEFAULT_CERTIFICATE_TITLE
from apps.certificates.text import render_bangla_image, wrap_text

GREEN = (15 / 255, 61 / 255, 46 / 255)
INK = (15, 61, 46, 255)


def _reader(path):
    if not path or not os.path.exists(path):
        return None
    return ImageReader(path)


def _draw_fitted(pdf, path, x, y, width, height):
    reader = _reader(path)
    if reader is None:
        return
    pdf.drawImage(reader, x, y, width=width, height=height, preserveAspectRatio=True, mask="auto", anchor="c")


def _draw_bangla(pdf, text, center_x, top_y, font_size, max_width, color=INK, align="center"):
    font_path = settings.BANGLA_FONT_PATH
    y = top_y
    for line in wrap_text(text, font_path, font_size * 3, max_width * 3):
        image = render_bangla_image(line, font_path=font_path, font_size=font_size * 3, color=color)
        draw_w = image.width / 3
        draw_h = image.height / 3
        if align == "center":
            x = center_x - draw_w / 2
        elif align == "right":
            x = center_x - draw_w
        else:
            x = center_x
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        pdf.drawImage(ImageReader(buffer), x, y - draw_h, draw_w, draw_h, mask="auto")
        y -= draw_h + 2
    return y


def render_certificate_pdf(certificate):
    winner = certificate.winner
    student = winner.student
    session = certificate.scholarship_session
    branding = session.branding
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4, pageCompression=0)
    width, height = A4
    pdf.setTitle(certificate.certificate_number)
    pdf.setStrokeColorRGB(*GREEN)
    pdf.setLineWidth(2)
    pdf.rect(18, 18, width - 36, height - 36)
    pdf.setLineWidth(0.6)
    pdf.rect(24, 24, width - 48, height - 48)

    logo = branding.logo.path if branding.logo else str(settings.BASE_DIR / "static/images/logo-fallback.png")
    sponsor = branding.sponsor_logo.path if branding.sponsor_logo else str(settings.BASE_DIR / "static/images/sponsor-fallback.png")
    _draw_fitted(pdf, logo, 48, height - 130, 78, 78)
    _draw_fitted(pdf, sponsor, width - 126, height - 130, 78, 78)

    y = height - 150
    title = branding.certificate_title_bn or DEFAULT_CERTIFICATE_TITLE
    y = _draw_bangla(pdf, title, width / 2, y, 22, 360)
    y -= 6
    y = _draw_bangla(pdf, branding.name_bn, width / 2, y, 16, 420)
    if branding.name_en:
        pdf.setFillColorRGB(*GREEN)
        pdf.setFont("Helvetica", 11)
        pdf.drawCentredString(width / 2, y - 4, branding.name_en)
        y -= 18
    if branding.sponsor_name_bn:
        y = _draw_bangla(pdf, branding.sponsor_name_bn, width / 2, y, 12, 360)
    y -= 8
    y = _draw_bangla(pdf, "এই সনদপত্র প্রদান করা হলো", width / 2, y, 12, 360)
    y -= 6
    y = _draw_bangla(pdf, student.name_bn, width / 2, y, 20, 400)

    if student.photo:
        try:
            _draw_fitted(pdf, student.photo.path, width - 150, y - 10, 70, 84)
        except (FileNotFoundError, ValueError):
            pass

    pdf.setFillColorRGB(0.1, 0.1, 0.1)
    pdf.setFont("Helvetica", 11)
    y -= 8
    pdf.drawCentredString(width / 2, y, f"ID: {student.student_id}")
    y -= 28
    details = [
        ("প্রতিষ্ঠান", student.institute.name_bn),
        ("শ্রেণি", student.academic_class.name_bn),
        ("বিভাগ", student.category_name_bn),
        ("পুরস্কার", winner.award_type.name_bn),
        ("সেশন", session.name_bn),
    ]
    for label, value in details:
        y = _draw_bangla(pdf, f"{label}: {value}", 70, y, 12, 430, align="left")
        y -= 2
    if winner.position:
        pdf.setFont("Helvetica", 11)
        pdf.drawString(70, y - 2, f"Position: {winner.position}")
        y -= 18
    issued = timezone.localtime(winner.published_at or certificate.generated_at)
    pdf.setFont("Helvetica", 10)
    pdf.drawString(70, y - 4, f"Date: {issued.strftime('%Y-%m-%d')}")
    pdf.drawRightString(width - 48, y - 4, certificate.certificate_number)
    y -= 28

    if branding.signature_image:
        _draw_fitted(pdf, branding.signature_image.path, 70, 78, 120, 50)
    if branding.seal_image:
        _draw_fitted(pdf, branding.seal_image.path, width - 170, 70, 70, 70)
    sign_top = 78
    if branding.signatory_name_bn:
        sign_top = _draw_bangla(pdf, branding.signatory_name_bn, 70, sign_top, 11, 180, align="left")
    if branding.signatory_title_bn:
        _draw_bangla(pdf, branding.signatory_title_bn, 70, sign_top, 10, 180, align="left")
    footer = branding.certificate_footer_bn or DEFAULT_CERTIFICATE_FOOTER
    _draw_bangla(pdf, footer, width / 2, 58, 9, 460)

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def bangla_image_has_ink(text):
    image = render_bangla_image(text, font_size=42)
    alpha = image.getchannel("A")
    _low, high = alpha.getextrema()
    return high > 0 and image.width > 10
