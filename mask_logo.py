import cv2
from google.cloud import vision
import numpy as np
from PIL import Image

def mask_logos_upper_area(image):
    try:
        from google.cloud import vision
        import io
        from PIL import ImageDraw

        client = vision.ImageAnnotatorClient()

        # Görüntüyü Vision API'ye uygun hale getir
        pil_image = Image.fromarray(image)
        byte_arr = io.BytesIO()
        pil_image.save(byte_arr, format='PNG')
        content = byte_arr.getvalue()

        vision_image = vision.Image(content=content)

        response = client.logo_detection(image=vision_image)
        logos = response.logo_annotations

        draw = ImageDraw.Draw(pil_image)
        #logoyu beyaz dikdörtgen ile çevreler
        for logo in logos:
            vertices = [(vertex.x, vertex.y) for vertex in logo.bounding_poly.vertices]
            if vertices:
                x_min = min([v[0] for v in vertices])
                y_min = min([v[1] for v in vertices])
                x_max = max([v[0] for v in vertices])
                y_max = max([v[1] for v in vertices])
                draw.rectangle([x_min, y_min, x_max, y_max], fill='white')

        return np.array(pil_image)

    except Exception as e:
        print(f"⚠️ Logo maskeleme sırasında hata oluştu, işlem atlandı: {e}")
        return image  # Hata durumunda orijinal resmi geri döndür
