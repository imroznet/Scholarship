import csv
from io import BytesIO

from django.http import HttpResponse
from openpyxl import Workbook
from openpyxl.styles import Font

from apps.verification.statuses import VerificationStatus

EXPORT_LIMIT = 5000
FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

OPERATOR_COLUMNS = [
    ("student_id", "শিক্ষার্থী আইডি"),
    ("name_bn", "নাম (বাংলা)"),
    ("name_en", "নাম (ইংরেজি)"),
    ("mobile", "মোবাইল"),
    ("institute", "প্রতিষ্ঠান"),
    ("academic_class", "শ্রেণি"),
    ("category", "বিভাগ"),
    ("upazila", "উপজেলা"),
    ("district", "জেলা"),
    ("verification_status", "যাচাই"),
]

ADMIN_EXTRA_COLUMNS = [
    ("date_of_birth", "জন্ম তারিখ"),
    ("father_name", "পিতার নাম"),
    ("father_mobile", "পিতার মোবাইল"),
    ("mother_name", "মাতার নাম"),
    ("mother_mobile", "মাতার মোবাইল"),
    ("village", "গ্রাম"),
    ("post_office", "ডাকঘর"),
    ("session", "সেশন"),
    ("registered_by", "নিবন্ধনকারী"),
]

WINNER_COLUMNS = [
    ("student_id", "শিক্ষার্থী আইডি"),
    ("name_bn", "নাম"),
    ("institute", "প্রতিষ্ঠান"),
    ("academic_class", "শ্রেণি"),
    ("category", "বিভাগ"),
    ("award", "পুরস্কার"),
    ("position", "অবস্থান"),
    ("amount", "পরিমাণ"),
    ("published", "প্রকাশিত"),
]


def sanitize_spreadsheet(value):
    if value is None:
        return ""
    text = str(value)
    if text.startswith(FORMULA_PREFIXES):
        return "'" + text
    return text


def student_columns(user):
    if user.is_super_admin:
        return OPERATOR_COLUMNS + ADMIN_EXTRA_COLUMNS
    return list(OPERATOR_COLUMNS)


def _student_value(student, key):
    if key == "institute":
        return student.institute.name_bn
    if key == "academic_class":
        return student.academic_class.name_bn
    if key == "category":
        return student.category_name_bn
    if key == "verification_status":
        return VerificationStatus(student.verification_status).label
    if key == "session":
        return student.scholarship_session.name_bn
    if key == "registered_by":
        return student.registered_by.username if student.registered_by else ""
    if key == "date_of_birth":
        return student.date_of_birth.isoformat()
    return getattr(student, key, "")


def student_rows(queryset, user):
    columns = student_columns(user)
    rows = []
    for student in queryset[:EXPORT_LIMIT]:
        rows.append([sanitize_spreadsheet(_student_value(student, key)) for key, _label in columns])
    return [label for _key, label in columns], rows


def winner_rows(queryset):
    rows = []
    for winner in queryset[:EXPORT_LIMIT]:
        student = winner.student
        values = [
            student.student_id,
            student.name_bn,
            student.institute.name_bn,
            student.academic_class.name_bn,
            student.category_name_bn,
            winner.award_type.name_bn,
            winner.position or "",
            winner.scholarship_amount if winner.scholarship_amount is not None else "",
            "হ্যাঁ" if winner.is_published else "না",
        ]
        rows.append([sanitize_spreadsheet(value) for value in values])
    return [label for _key, label in WINNER_COLUMNS], rows


def csv_response(filename, headers, rows):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return response


def xlsx_response(filename, headers, rows):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Report"
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    for cell in sheet[1]:
        cell.font = Font(bold=True)
    payload = BytesIO()
    workbook.save(payload)
    response = HttpResponse(
        payload.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
