import pytesseract
import re
from config import TESSERACT_CMD
from numba.core.typing.builtins import Print
from sympy.physics.units import amount
from ner_extractor import extract_name

pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
from patterns import (pattern_establishment_code, pattern_certificate_number, pattern_identity_number,
                      pattern_validity_date, pattern_print_place_date, pattern_revision_date_and_no,pattern_company_name,pattern_company_name_alt,pattern_certificate_scope_product,pattern_certificate_scope_amount,pattern_certificate_type,pattern_company_name_type6)


# def extract_text(image, lang='tur'):
#     return pytesseract.image_to_string(image, lang=lang)
#
# def find_patterns(text):
#     results = {}
#     results['establishment_code'] = re.findall(pattern_establishment_code, text, re.MULTILINE | re.IGNORECASE)
#     results['certificate_number'] = re.findall(pattern_certificate_number, text, re.MULTILINE | re.IGNORECASE)
#     results['identity_number'] = re.findall(pattern_identity_number, text, re.MULTILINE | re.IGNORECASE)
#     results['validity_date'] = re.findall(pattern_validity_date, text, re.MULTILINE | re.IGNORECASE)
#     results['print_place_date'] = re.findall(pattern_print_place_date, text, re.MULTILINE | re.IGNORECASE)
#     return results

def extract_company_name_from_text(text):
    lines = text.split("\n")
    company_lines = []
    is_between = False

    for line in lines:
        # Revizyon geçince başlasın
        if re.search(pattern_revision_date_and_no, line, re.IGNORECASE):
            is_between = True
            continue

        if is_between and (
                re.search(pattern_certificate_type, line, re.IGNORECASE) or
                re.search(pattern_certificate_scope_product, line, re.IGNORECASE) or
                re.search(pattern_certificate_scope_amount, line, re.IGNORECASE)
        ):
            break

        if is_between:
            company_lines.append(line)

    combined = " ".join(company_lines).strip()
    combined = re.sub(r"\s*\n\s*", " ", combined)

    company_mid_parts = [
        r"T[ÄA]R", r"[ÜU]R[ÜU]N", r"P[ÄA]Z", r"S[ÄA]N", r"T[İI1]C", r"[İI1]TH", r"[İI1]HR",
        r"G[İI1]DA", r"HAYVANC[İI1]L[İI1]K", r"MADENC[İI1]L[İI1]K", r"TUR[İI1]ZM", r"[İI1]N[ŞS]",
        r"NAKL[İI1]YAT?", r"OTO", r"ELEKTR[İI1]K", r"ENERJ[İI1]", r"TEKST[İI1]L", r"SANAY[İI1]", r"T[ÜU]R", r"T[İI1]CARET"
    ]
    company_suffixes = r"(?:LTD\.?\s*ŞTİ\.?|LTD\.?|ŞTİ\.?|A[,\.]?\s*Ş\.?|A\.Ş\.?|ANON[İI]M\s+Ş[İI]RKET[İI]?|L[İI]M[İI]TED\s+Ş[İI]RKET[İI]?|KOOPERAT[İI]F|KOOP\.?|VAKFI|DERNEĞ[İI]|SEND[İI]KASI)"
    pattern = rf"([A-ZÇŞĞÜÖİa-zçşğüöı0-9\s,&\-\.]{{5,}}?(?:(?:{'|'.join(company_mid_parts)})\.?\s*)*(?:{company_suffixes})(?:\s+{company_suffixes})*)"

    matches = list(re.finditer(pattern, combined, re.IGNORECASE))

    if matches:
        company_name = max(matches, key=lambda m: len(m.group(0))).group(0).strip()
    else:
        fallback_match = re.search(
            r"([A-ZÇŞĞÜÖİ][A-ZÇŞĞÜÖİ\s]{2,})",
            combined,
            re.IGNORECASE
        )
        company_name = fallback_match.group(1).strip() if fallback_match else combined if combined else None

    return company_name

def extract_text(image, lang='tur'):
    return pytesseract.image_to_string(image, lang=lang)

#tarih içerisindeki boşluk karakterleri temizleme
def clean_date_format(text):
    text = re.sub(r'([./-])\s+', r'\1', text)
    text = re.sub(r'\s+([./-])', r'\1', text)
    return text

def find_patterns(text, results,predicted_type):
    if not results['establishment_code']:
        establishment_code_match = re.search(pattern_establishment_code, text, re.MULTILINE | re.IGNORECASE)
        if establishment_code_match:
            results['establishment_code'] = establishment_code_match.groups()

    if not results['certificate_number']:
        certificate_number_match = re.search(pattern_certificate_number, text, re.MULTILINE | re.IGNORECASE)
        if certificate_number_match:
            results['certificate_number'] = certificate_number_match.groups()

    if not results['validity_date']:
        text_for_date = clean_date_format(text)
        match = re.search(pattern_validity_date, text_for_date, re.MULTILINE | re.IGNORECASE)
        if match:
            results['validity_date'] = match.groups()

    if not results['revision_date']:
        revision_date_match = re.search(pattern_revision_date_and_no, text, re.MULTILINE | re.IGNORECASE)
        if revision_date_match:
            results['revision_date'] = revision_date_match.group(2).strip()

    if not results['company_name']:
        company_name = None
        if str(predicted_type).strip() == "type_6":
            m = re.search(pattern_company_name_type6, text, re.IGNORECASE)
            if m:
                company_name = m.group(2).strip()
        elif str(predicted_type).strip() == "type_4" and extract_name is not None:
            try:
                company_name = extract_name(text)
            except Exception:
                company_name = None  # NER hata verirse regex'e düş
        # NER sonuç vermezse veya Type-4 değilse: mevcut yöntem
        if not company_name:
            company_name = extract_company_name_from_text(text)

        if company_name:
            results['company_name'] = company_name

    if not results['certificate_scope_product']:
        match = re.search(pattern_certificate_scope_product, text, re.MULTILINE | re.IGNORECASE)
        if match:
            results['certificate_scope_product'] = match.group(1).strip()

    if not results['certificate_scope_amount']:
        match = re.search(pattern_certificate_scope_amount, text, re.MULTILINE | re.IGNORECASE)
        if match:
            results['certificate_scope_amount'] = match.group(2).strip()

    if not results.get('certificate_type'):
        type_match = re.search(pattern_certificate_type, text, re.IGNORECASE)
        if type_match:
            results['certificate_type'] = type_match.group(1).upper()

    return results