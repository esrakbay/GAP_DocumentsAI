
from pdf2image import convert_from_path

pdf_path = r'C:\Users\ekalay\Desktop\703376DM.PDF'
poppler_path = r'C:\Poppler\poppler-24.08.0\Library\bin'

images = convert_from_path(pdf_path, poppler_path=poppler_path)

for i, img in enumerate(images):
    img.save(f'page_{i+1}.png', 'PNG')
