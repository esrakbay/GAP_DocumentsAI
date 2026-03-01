import cv2
import pytesseract
import pandas as pd
from collections import defaultdict
from config import TESS_DATA_CONFIG, TESS_LANG
from image_processing import preprocess_image

def fix_header_with_fallback(df):
    header = df.iloc[0].tolist()
    fallback = df.iloc[1].tolist()

    fixed_header = []
    for i, val in enumerate(header):
        if pd.isna(val) or str(val).strip() == "":
            fixed_header.append(str(fallback[i]).strip())
        else:
            fixed_header.append(str(val).strip())

    df.columns = fixed_header
    df = df[1:].reset_index(drop=True)
    return df

def table_data_extraction(image):
    if image is None or image.size == 0:
        print("⚠️ preprocess_image: Görüntü boş, işleme alınmadı.")
        return None

    processed_image = preprocess_image(image)
    cv2.imwrite("preprocessed_cropped_table_debug.jpg", processed_image)
    config = TESS_DATA_CONFIG
    ocr_data = pytesseract.image_to_data(processed_image, config=config, lang=TESS_LANG, output_type=pytesseract.Output.DICT)
    raw_text = pytesseract.image_to_string(processed_image, config=config, lang=TESS_LANG)
    print("\n📄 OCR HAM METİN:\n", raw_text)
    rows = []
    current_row = []
    all_rows = []

    for i in range(len(ocr_data['text'])):
        text = ocr_data['text'][i].strip()
        x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]
        print(f"OCR: x={x}, y={y}, text='{text}'")  # debug satırı
        all_rows.append((x, y, text, w))

        if current_row and text != '' and all_rows[i-1][2] != '':
            combined_text = current_row[-1][2] + " " + text
            current_row[-1] = (current_row[-1][0], current_row[-1][1], combined_text, current_row[-1][3])
        elif text != '':
            current_row.append((x, y, text, w))

        if current_row and abs(y - current_row[0][1]) > 20:
            rows.append(sorted(current_row, key=lambda item: item[0]))
            current_row = []

    if current_row:
        rows.append(sorted(current_row, key=lambda item: item[0]))

    updated_matrix = [[None for _ in row] for row in rows]

    for i1, row1 in enumerate(rows):
        for j1, (x1, y1, text1, w1) in enumerate(row1):
            combined_text = text1
            combined_w = w1
            combined_x, combined_y = x1, y1

            for i2, row2 in enumerate(rows[i1:], start=i1):
                start_index = j1 + 1 if i1 == i2 else 0
                for j2, (x2, y2, text2, w2) in enumerate(row2[start_index:], start=start_index):
                    if abs(x1 - x2) == abs(y1 - y2):
                        combined_text += " " + text2
                        combined_y = (y1 + y2) // 2
                        combined_x = (x1 + x2) // 2
                        combined_w = max(combined_w, w2)
                        updated_matrix[i2][j2] = (x2, y2, "", w2)
                        del(rows[i2][j2])
                        del(updated_matrix[i2][j2])

            updated_matrix[i1][j1] = (combined_x, combined_y, combined_text, combined_w)

    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            if updated_matrix[i][j] is None:
                updated_matrix[i][j] = cell

    for i in range(len(rows)):
        for j in range(len(rows[i])):
            rows[i][j] = updated_matrix[i][j]

    sorted_matrix = []
    threshold_y = 50

    rows_dict = defaultdict(list)
    for row in rows:
        if not row:
            continue  # boş satır varsa atla
        for x, y, text, w in row:
            row_key = y // threshold_y
            rows_dict[row_key].append((x, text))

    for row_key in sorted(rows_dict.keys()):
        sorted_row = sorted(rows_dict[row_key], key=lambda item: item[0])
        row_data = [text for _, text in sorted_row]
        sorted_matrix.append(row_data)

    df = pd.DataFrame(sorted_matrix)
    df = fix_header_with_fallback(df)
    return df
