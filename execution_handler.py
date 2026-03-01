import numpy as np
import pandas as pd

from pdf_to_image import pdf_to_images
from image_processing import preprocess_image
#from sympy.codegen.ast import continue_
from text_extraction import extract_text, find_patterns
from table_crop import table_detection_and_crop
from table_extraction import table_data_extraction
from mask_logo import mask_logos_upper_area
from predict_pdf_file import predict_pdf_type

from extractors import extract_type1, extract_type2,extract_type4,extract_type6

def handle_document(pdf_path, poppler_path):
    doc_type, _ = predict_pdf_type(pdf_path,poppler_path)
    pages = pdf_to_images(pdf_path, dpi=600, poppler_path=poppler_path)
    table_df = pd.DataFrame()
    extracted_data = {
        'establishment_code': None,
        'certificate_number': None,
        'identity_number': None,
        'validity_date': None,
        'print_place_date': None,
        'revision_date': None,
        'company_name': None,
        'certificate_scope_product': None,
        'certificate_scope_amount': None
    }
    found_flags = {key: False for key in extracted_data.keys()}

    if doc_type == "type_1" or doc_type == "type_3":
        image = np.array(pages[0])

        try:
            masked_image = mask_logos_upper_area(image)
        except Exception as e:
            print("⚠️ Logo maskelenemedi, orijinal görüntü kullanılacak:", e)
            masked_image = image

        try:
            processed_image = preprocess_image(masked_image)
        except Exception as e:
            print("⚠️ Görüntü işleme başarısız:", e)

        text = extract_text(processed_image, lang='tur')
        print(text)
        extracted_data = find_patterns(text, extracted_data,doc_type)
        extracted_data, table_df = extract_type1(extracted_data, found_flags, masked_image)

    elif doc_type == "type_2":
        image = np.array(pages[0])
        try:
            masked_image = mask_logos_upper_area(image)
        except Exception:
            masked_image = image

        try:
            processed_image = preprocess_image(masked_image)
        except Exception as e:
            print("⚠️ Görüntü işleme başarısız:", e)

        text = extract_text(processed_image, lang='tur')
        print(text)
        extracted_data = find_patterns(text, extracted_data,doc_type)
        extracted_data, table_df = extract_type2(extracted_data)

    elif doc_type == "type_4":
        image = np.array(pages[0])
        try:
            masked_image = mask_logos_upper_area(image)
        except Exception:
            masked_image = image

        try:
            processed_image = preprocess_image(masked_image)
        except Exception as e:
            print("⚠️ Görüntü işleme başarısız:", e)

        text = extract_text(processed_image, lang='tur')
        print(text)
        extracted_data = find_patterns(text, extracted_data,doc_type)
        extracted_data, table_df = extract_type4(extracted_data)

    elif doc_type == "type_6":
        image = np.array(pages[0])
        try:
            masked_image = mask_logos_upper_area(image)
        except Exception:
            masked_image = image

        try:
            processed_image = preprocess_image(masked_image)
        except Exception as e:
            print("⚠️ Görüntü işleme başarısız:", e)

        text = extract_text(processed_image, lang='tur')
        print(text)
        extracted_data = find_patterns(text, extracted_data,doc_type)
        extracted_data, table_df = extract_type6(extracted_data)
    else:
        raise ValueError(f"Unsupported doc type: {doc_type}")

    return extracted_data, table_df
