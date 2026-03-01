import cv2
import numpy as np

def preprocess_image(image):

    if image is None or image.size == 0:
        print("⚠️ preprocess_image: Görüntü boş, işleme alınmadı.")
        return None
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    processed_image = cv2.dilate(binary, kernel, iterations=1)
    processed_image = cv2.erode(processed_image, kernel, iterations=1)

    return processed_image
