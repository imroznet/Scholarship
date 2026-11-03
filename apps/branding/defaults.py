"""Reset and bootstrap defaults.

Templates always read branding from the database. These values are used only
when a session is first created or when a super admin explicitly resets branding.
"""

DEFAULT_SHORT_NAME = "CGS"
DEFAULT_SPONSOR_NAME_BN = "কান্ট্রি গ্রুপ"
DEFAULT_SPONSOR_NAME_EN = "Country Group"
DEFAULT_CERTIFICATE_TITLE = "সনদপত্র"
DEFAULT_CERTIFICATE_FOOTER = "এই সনদপত্র সংশ্লিষ্ট স্কলারশিপ সেশনের পরিচয় অনুসারে ইস্যু করা হয়েছে।"


def initial_branding_kwargs(session):
    return {
        "name_bn": session.name_bn,
        "name_en": session.name_en,
        "short_name": DEFAULT_SHORT_NAME,
        "description_bn": session.description,
        "sponsor_name_bn": "",
        "sponsor_name_en": "",
        "certificate_title_bn": DEFAULT_CERTIFICATE_TITLE,
        "certificate_footer_bn": DEFAULT_CERTIFICATE_FOOTER,
    }


def reset_branding_values(session):
    return {
        "name_bn": session.name_bn,
        "name_en": session.name_en,
        "short_name": DEFAULT_SHORT_NAME,
        "slogan_bn": "",
        "description_bn": session.description,
        "contact_info": "",
        "email": "",
        "phone": "",
        "address": "",
        "sponsor_name_bn": DEFAULT_SPONSOR_NAME_BN,
        "sponsor_name_en": DEFAULT_SPONSOR_NAME_EN,
        "sponsor_description": "",
        "sponsor_website": "",
        "sponsor_contact": "",
        "certificate_title_bn": DEFAULT_CERTIFICATE_TITLE,
        "certificate_footer_bn": DEFAULT_CERTIFICATE_FOOTER,
        "signatory_name_bn": "",
        "signatory_title_bn": "",
    }
