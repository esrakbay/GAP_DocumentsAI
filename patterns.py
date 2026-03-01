# Kuruluş kodu | KSK kodu
#pattern_establishment_code = r"(?i)(kuruluş|kurulus|ksk)\s*(kodu|kod|no|nu)?\s*[':–\-]?\s*(T\s*R\s*\.?\s*İ?\s*T?\s*U?\.?\s*\d+)"
pattern_establishment_code = (
    r"(?i)"
    r"(?:\b(kuruluş|kurulus|ksk)\s*(kodu|kod|no|nu)?\s*[':–\-]?\s*)?"
    r"(T\s*R\s*\.?\s*(?:[İI1]\s*){1,2}\s*T?\s*U?\.?\s*\d+)"
)

# Sertifika numarası
#pattern_certificate_number = r"(?i)(sertifika\s*(numarası|no)?)\s*[:\-*']?\s*((?:T\s*R\s*\.?\s*İ?\s*T?\s*U?\.?\s*\d+)[\w./\-]*)"
#pattern_certificate_number = (
#    r"(?i)"
#    r"(sertifika.*?(numarası|no))"          # Etiket
#    r".*?"                                  # arada ne olursa olsun (boşluk, bullet, tire, vs.)
#    r"(TR.*?\d{2,5}(?:[-–—]\d+)+)"          # TR ile başlayan numara bloğu
#)
pattern_certificate_number = r"(?i)(sertifika.*?(numarası|no)).*?(TR.*?\d{2,5}(?:[-–—/.]\d+)+)"
# Kimlik veya Vergi Numarası (10 haneli)
pattern_identity_number = r"(?i)(tc\s*kimlik|vergi\s*no|tc\s*kimlik\s*/\s*vergi\s*no)\s*[:\-]?\s*(\d{10})"

# Geçerlilik tarihi
#pattern_validity_date = r"(?i)(geçerlilik\s*tarihi\s*[:\-]*|bu\s*sertifika\s*)(\d{1,2}\s*[./-]\s*\d{1,2}\s*[./-]\s*\d{4})(\s*tarihine\s*kadar\s*geçerlidir)?"
pattern_validity_date = r"(?i)(ge[cç]erlilik\s*tarihi\s*[:\-]*|bu\s*sertifika\s*,?\s*)(\d{1,2}[./-]\d{1,2}[./-]\d{4})(\s*tarihine\s*kadar\s*ge[cç]erlidir)?"
# Basım yeri ve tarihi
pattern_print_place_date = r"(?i)(basım\s*yeri\s*/\s*tarihi)\s*[:\-]?\s*([A-ZÇŞĞÜÖİa-zçşğüöı\s]+)\s*-\s*([0-9]{2}\.[0-9]{2}\.[0-9]{4})"

# Revizyon tarihi ve no
pattern_revision_date_and_no = r"(?i)(rev(?:izyon)?(?:\s*no)?(?:\s*/\s*tarihi|\s*tarih\s*ve\s*no|\s*no\s*ve\s*tarihi)?(?:'?[a-z]{0,3})?)\s*[:\-–]?\s*[^0-9]*([0-9][0-9A-Za-z./\-]*)"


# Şirket/Grup adı
pattern_company_name = r"(?i)(üretici\s*grubunun\s*adı|üretici\s*.\s*müteşebbis)\s*[:\-]?\s*(.+)"

pattern_company_name_type6 = r"(?ims)^\s*(üretici\s*(?:[\/•·]\s*üretici\s*örgütü)?(?:[\/•·]\s*müteşebbis)?\s*adı)\s*[:：]?\s*[\r\n]+\s*([^\r\n]+?)\s*(?:\r?\n|$)"

pattern_company_name_alt = r"\n\s*([A-ZÇŞĞÜÖİ0-9][A-ZÇŞĞÜÖİa-zçşğüöı\s.,&\-()\/]{5,})\s+ŞTİ\.?"

# Kapsamdaki ürünler
pattern_certificate_scope_product = r"(?i)sertifika\s*kapsamındaki\s*ürün\s*[:\-]?\s*((?:.|\n)*?)(?=\n?\s*ürün\s*m[iİ]ktarı)"

# Ürün miktarı
# pattern_certificate_scope_amount = r"(?i)(ürün\s*m[ıiİİ]k?t?a?r[ıi])\s*[:：]?\s*((?:[^0-9\s]{0,2}?\d{2,5}\s*TON[,.\s]*)+)"
pattern_certificate_scope_amount = r"""(?isx)
    (ürün \s* m[ıiİi]k?t?a?r[ıiİi])     # Grup 1: başlık
    \s*[:：]?\s*
    (                                   # Grup 2: miktar listesi
        (?:
            [^\w]??                     
            (?:
                \d{1,3}(?:[.,\s]\d{3})* # 2.471, 2 471, 2471
                |\d+                    
            )
            (?:[.,]\d+)?                
            \s*
            (?:T \s* O \s* N|K \s* G)?  
            (?:                         
                \s+
                [A-ZÇĞİÖŞÜa-zçğıöşü\-]+
                (?:\s+[A-ZÇĞİÖŞÜa-zçğıöşü\-]+){0,3}
            )?
            (?:\s*[;,]\s*|\s+|$)        
        )+
    )
    (?=\s*(?:Üretim|Hasat|Sertifika|Revizyon|Firma|$))  # Burada DUR
"""
# sertifika türü
pattern_certificate_type = r"\(?\b(B[iİ]REYSEL|GRUP)\b\)?"

# === Ana sözlük ===
ALL_PATTERNS = {
    "establishment_code": pattern_establishment_code,
    "certificate_number": pattern_certificate_number,
    "identity_number": pattern_identity_number,
    "validity_date": pattern_validity_date,
    "print_place_date": pattern_print_place_date,
    "revision_date": pattern_revision_date_and_no,
    "company_name": pattern_company_name,
    "company_name_alt": pattern_company_name_alt,
    "certificate_scope_product": pattern_certificate_scope_product,
    "certificate_scope_amount": pattern_certificate_scope_amount,
    "certificate_type": pattern_certificate_type,
    "company_name_type6": pattern_company_name_type6

}

