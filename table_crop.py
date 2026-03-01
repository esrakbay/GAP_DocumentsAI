from requests import delete
from ultralyticsplus import YOLO, render_result
import cv2
import numpy as np
import os
import json
import ssl
import pytesseract
import pandas as pd
from config import MODEL_PATH,MODEL_CONFIDENCE_THRESHOLD,MODEL_IOU_THRESHOLD,MODEL_MAXIMUM_NUMBER_OF_DETECTION,MODEL_NMS_CLASS_AGNOSTIC
from torch.serialization import add_safe_globals
from ultralytics.nn.tasks import DetectionModel
add_safe_globals([DetectionModel])

def table_detection_and_crop(original_image):
    model = YOLO(MODEL_PATH)
    ssl._create_default_https_context = ssl._create_unverified_context
    model.overrides['conf'] = MODEL_CONFIDENCE_THRESHOLD
    model.overrides['iou'] = MODEL_IOU_THRESHOLD
    model.overrides['agnostic_nms'] = MODEL_NMS_CLASS_AGNOSTIC
    model.overrides['max_det'] = MODEL_MAXIMUM_NUMBER_OF_DETECTION

    results = model.predict(original_image)
    if not results or not results[0].boxes or len(results[0].boxes) == 0:
        print("⚠️ Tablo tespiti yapılamadı.")
        return None

    box = results[0].boxes[0].xyxy
    x1, y1, x2, y2 = map(int, box[0])
    image_cropped = original_image[y1:y2, x1:x2]

    if image_cropped.shape[0] == 0 or image_cropped.shape[1] == 0:
        print("⚠️ Kırpılmış tablo resmi boş.")
        return None

    gray_image = cv2.cvtColor(image_cropped, cv2.COLOR_BGR2GRAY)
    adaptive_binary_image = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                                  cv2.THRESH_BINARY_INV, 15, 10)
    gaussian_blur = cv2.GaussianBlur(adaptive_binary_image, (5, 5), 0)
    edges = cv2.Canny(gaussian_blur, 50, 150, apertureSize=3)
    edges_for_long_lines = cv2.Canny(edges, 50, 150, apertureSize=3)
    lines_for_long_detection = cv2.HoughLinesP(edges_for_long_lines, 1, np.pi / 180, threshold=100,
                                               minLineLength=500, maxLineGap=10)

    top_line_y = None
    bottom_line_y = None

    if lines_for_long_detection is not None:
        for line in lines_for_long_detection:
            x1, y1, x2, y2 = line[0]
            if abs(y1 - y2) < 10:
                if top_line_y is None or y1 < top_line_y:
                    top_line_y = y1
                if bottom_line_y is None or y1 > bottom_line_y:
                    bottom_line_y = y1

    if top_line_y is not None and bottom_line_y is not None:
        cropped_image = image_cropped[top_line_y+5:bottom_line_y-5, :]
    elif top_line_y is not None:
        cropped_image = image_cropped[top_line_y+5:, :]
    elif bottom_line_y is not None:
        cropped_image = image_cropped[:bottom_line_y-5, :]
    else:
        cropped_image = image_cropped

    if cropped_image.shape[0] == 0 or cropped_image.shape[1] == 0:
        print("⚠️ İç kırpma sonrası tablo resmi boş.")
        return None

    return table_detection_and_crop_y(cropped_image)

def table_detection_and_crop_y(original_image):
    model = YOLO(MODEL_PATH)
    ssl._create_default_https_context = ssl._create_unverified_context
    model.overrides['conf'] = MODEL_CONFIDENCE_THRESHOLD
    model.overrides['iou'] = MODEL_IOU_THRESHOLD
    model.overrides['agnostic_nms'] = MODEL_NMS_CLASS_AGNOSTIC
    model.overrides['max_det'] = MODEL_MAXIMUM_NUMBER_OF_DETECTION

    results = model.predict(original_image)
    if not results or not results[0].boxes or len(results[0].boxes) == 0:
        print("⚠️ table_detection_and_crop_y: Tablolara ait kutu bulunamadı.")
        return None

    box = results[0].boxes[0].xyxy
    x1, y1, x2, y2 = map(int, box[0])
    image_cropped = original_image[y1:y2, x1:x2]

    if image_cropped.shape[0] == 0 or image_cropped.shape[1] == 0:
        print("⚠️ table_detection_and_crop_y: Kırpılmış tablo görüntüsü boş.")
        return None

    gray_image = cv2.cvtColor(image_cropped, cv2.COLOR_BGR2GRAY)
    adaptive_binary_image = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                                  cv2.THRESH_BINARY_INV, 15, 10)
    gaussian_blur = cv2.GaussianBlur(adaptive_binary_image, (5, 5), 0)
    edges = cv2.Canny(gaussian_blur, 50, 150, apertureSize=3)
    edges_for_long_lines = cv2.Canny(edges, 50, 150, apertureSize=3)
    lines_for_long_detection = cv2.HoughLinesP(edges_for_long_lines, 1, np.pi / 180, threshold=100,
                                               minLineLength=500, maxLineGap=10)

    top_line_y = None
    bottom_line_y = None

    if lines_for_long_detection is not None:
        for line in lines_for_long_detection:
            x1, y1, x2, y2 = line[0]
            if abs(y1 - y2) < 10:
                if top_line_y is None or y1 < top_line_y:
                    top_line_y = y1
                if bottom_line_y is None or y1 > bottom_line_y:
                    bottom_line_y = y1

    if bottom_line_y is not None:
        cropped_image = image_cropped[:bottom_line_y - 5, :]
    else:
        cropped_image = image_cropped

    if cropped_image.shape[0] == 0 or cropped_image.shape[1] == 0:
        print("⚠️ table_detection_and_crop_y: İç kırpma sonrası görüntü boş.")
        return None

    cv2.imwrite("cropped_table_debug.jpg", cropped_image)
    return cropped_image
