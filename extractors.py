# extractor.py
# -*- coding: utf-8 -*-

import re
import pandas as pd
from rapidfuzz import process, fuzz

from table_crop import table_detection_and_crop
from table_extraction import table_data_extraction


# --- Bilinen ürün listesi (eşleştirme için) ---
known_products_raw = """
ELMA, LİMON, PORTAKAL, MANDALİNA, DOMATES, SALATALIK, BİBER, MUZ, ÜZÜM, PATATES,
KARPUZ, KAVUN, ÇİLEK, KİRAZ, VİŞNE, NAR, AYVA, ERİK, ŞEFTALİ, NEKTARİN, ARMUT,
GREYFURT, ANANAS, HURMA, KARNABAHAR, BROKOLİ, MARUL, ROKA, TURP, LAHANA,
ISPANAK, PAZI, HAVUÇ, SOĞAN, SARIMSAK, BEZELYE, FASULYE, BARBUNYA, NOHUT,
MERCİMEK, MISIR, BUĞDAY, ARPA, YULAF, ÇAVDAR, REZENE, MAYDANOZ, DEREOTU, NANE, ALTINTOP
"""
known_products = [item.strip() for item in known_products_raw.upper().split(",")]


# --- Ürün–miktar çıkarımı (gelişmiş) ---
def extract_product_amount_pairs(text: str, known_product_list):
    """
    'Ürün miktarı' benzeri serbest metinden [(Ürün, Miktar)] döndürür.
    - "2471,932 ton Kavun" gibi miktar-önce kalıpları
    - "Kavun 2471,932 ton" gibi ürün-önce kalıpları
    - Çoklu ürünleri virgül/boşluk ayraçlarıyla taşmadan yakalar
    """
    pairs = []
    if not text:
        return pairs

    # Sayı (1.234,56 | 2471,932 | 500 | 400TON gibi varyantlar) + birim
    NUM = r"(?:\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?|\d+(?:[.,]\d+)?)"
    UNIT = r"(?:ton|kg|adet)\b"

    # Ürün adı: en fazla 4 kelime, harf ve tire içerebilir
    PROD = r"[A-Za-zÇĞİÖŞÜçğıöşü\-]+(?:\s+[A-Za-zÇĞİÖŞÜçğıöşü\-]+){0,3}"

    # 1) Miktar önce: "2471,932 ton Kavun"
    rx_qty_first = re.compile(
        rf"(?P<qty>{NUM})\s*(?P<unit>{UNIT})"
        rf"(?:\s+(?P<prod>{PROD}))?"
        r"(?=,|;|\.|\)|\s|$)",
        re.IGNORECASE
    )

    # 2) Ürün önce: "Kavun 2471,932 ton"
    rx_prod_first = re.compile(
        rf"(?P<prod>{PROD})\s+(?P<qty>{NUM})\s*(?P<unit>{UNIT})"
        r"(?=,|;|\.|\)|\s|$)",
        re.IGNORECASE
    )

    # Metni tek satır gibi işle, ama ayırıcıları koru
    blob = text.replace("\n", " ")

    def norm_amount(qty_str: str) -> str:
        # 1.234,56 -> 1234.56 ; 2471,932 -> 2471.932
        return qty_str.replace(".", "").replace(",", ".")

    def canon_prod(prod_str: str) -> str:
        prod = (prod_str or "").strip().upper()
        if not prod:
            return ""
        best = process.extractOne(prod, known_product_list, scorer=fuzz.token_sort_ratio)
        if best and best[1] >= 85:
            return best[0]
        return prod

    # Önce "miktar önce" eşleşmeler
    for m in rx_qty_first.finditer(blob):
        qty = norm_amount(m.group("qty"))
        unit = m.group("unit").upper()
        prod = canon_prod(m.group("prod") or "")
        # Ürün adı verilmemişse boş bırak
        pairs.append((prod, f"{qty} {unit}"))

    # Sonra "ürün önce" eşleşmeler (varsa aynı ürünü tekrar eklememek için hafif filtre)
    seen = set((p[0], p[1]) for p in pairs)
    for m in rx_prod_first.finditer(blob):
        qty = norm_amount(m.group("qty"))
        unit = m.group("unit").upper()
        prod = canon_prod(m.group("prod") or "")
        item = (prod, f"{qty} {unit}")
        if item not in seen:
            pairs.append(item)
            seen.add(item)

    return pairs


# --- Yardımcı normalize ---
def normalize_list(text, is_amount=False, known_product_list=None):
    if not text:
        return []

    if is_amount:
        cleaned = text.replace("\n", " ").strip()

        # OCR hatalarını toparla (ör: 11İ5TON → 115 TON)
        cleaned = re.sub(r"([0-9İi]+)\s*(TON|KG)",
                         lambda m: m.group(1).replace("İ", "1") + " " + m.group(2),
                         cleaned, flags=re.IGNORECASE)

        # Sadece miktar+birim yakala
        matches = re.finditer(
            r"(\d{1,3}(?:[.,]\d{3})*|\d+)(?:[.,]\d+)?\s*(TON|KG)",
            cleaned, flags=re.IGNORECASE
        )

        results = []
        for m in matches:
            qty = m.group(1).replace(".", "").replace(",", ".")
            unit = m.group(2).upper()
            results.append(f"{qty} {unit}")

        return results

#bilinen ürün adları listelenir
    elif known_product_list:
        words = re.split(r"[, \n]+", text.upper())
        matched, seen = [], set()
        for word in words:
            if not word.strip():
                continue
            best = process.extractOne(word, known_product_list, scorer=fuzz.token_sort_ratio)
            if best and best[1] >= 85 and best[0] not in seen:
                matched.append(best[0])
                seen.add(best[0])
        return matched
    else:
        return [i.strip() for i in text.split(",") if i.strip()]
# --- Type 1 ---
def extract_type1(extracted_data, found_flags, masked_image):
    field_map = {
        'establishment_code': lambda v: v[2],
        'certificate_number': lambda v: v[2],
        'identity_number': lambda v: v[1],
        'validity_date': lambda v: v[1],
        'print_place_date': lambda v: f"{v[1].strip()} / {v[2]}",
        'revision_date': lambda v: v,
        'company_name': lambda v: v
    }

    for field, extractor in field_map.items():
        if extracted_data.get(field) and not found_flags[field]:
            try:
                print(f"{field.replace('_', ' ').title()}: {extractor(extracted_data[field])}")
                found_flags[field] = True
            except Exception as e:
                print(f"⚠️ Hata ({field}):", e)
#tablo çıkarımı
    try:
        cropped_image = table_detection_and_crop(masked_image)
        table_df = table_data_extraction(cropped_image)
    except Exception as e:
        print("⚠️ Tablo çıkarımında hata:", e)
        table_df = pd.DataFrame()

    return extracted_data, table_df


# --- Type 2 ---
def extract_type2(extracted_data):
    product_list = normalize_list(extracted_data.get("certificate_scope_product"), known_product_list=known_products)
    amount_list = normalize_list(extracted_data.get("certificate_scope_amount"), is_amount=True)
#tablo çıkarılamadıysa boş bir dataframe oluşturulur
    if not product_list and not amount_list:
        table_df = pd.DataFrame(columns=["Ürün", "Miktar"])
    else:
    #DataFrame oluşturulurken satırların hizalanması
        max_len = max(len(product_list), len(amount_list))
        product_list += [""] * (max_len - len(product_list))
        amount_list += [""] * (max_len - len(amount_list))

        table_df = pd.DataFrame({
            "Ürün": product_list,
            "Miktar": amount_list
        })

    return extracted_data, table_df


# --- Type 4 ---
def extract_type4(extracted_data):
    product_list = normalize_list(extracted_data.get("certificate_scope_product"), known_product_list=known_products)
    amount_list = normalize_list(extracted_data.get("certificate_scope_amount"), is_amount=True)

    if not product_list and not amount_list:
        table_df = pd.DataFrame(columns=["Ürün", "Miktar"])
    else:
        max_len = max(len(product_list), len(amount_list))
        product_list += [""] * (max_len - len(product_list))
        amount_list += [""] * (max_len - len(amount_list))

        table_df = pd.DataFrame({
            "Ürün": product_list,
            "Miktar": amount_list
        })

    return extracted_data, table_df


# --- Type 6 ---
def extract_type6(extracted_data):
    # 1) Önce gelişmiş çıkarımı dene
    pairs = extract_product_amount_pairs(
        extracted_data.get("certificate_scope_amount", "") or "",
        known_products
    )

    if pairs:
        table_df = pd.DataFrame(pairs, columns=["Ürün", "Miktar"])
        return extracted_data, table_df

    # 2) Olmazsa önceki basit normalize ile devam et
    product_list = normalize_list(extracted_data.get("certificate_scope_product"), known_product_list=known_products)
    amount_list = normalize_list(extracted_data.get("certificate_scope_amount"), is_amount=True)

    if not product_list and not amount_list:
        table_df = pd.DataFrame(columns=["Ürün", "Miktar"])
    else:
        max_len = max(len(product_list), len(amount_list))
        product_list += [""] * (max_len - len(product_list))
        amount_list += [""] * (max_len - len(amount_list))

        table_df = pd.DataFrame({
            "Ürün": product_list,
            "Miktar": amount_list
        })

    return extracted_data, table_df
