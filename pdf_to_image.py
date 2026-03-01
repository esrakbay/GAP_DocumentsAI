from pdf2image import convert_from_path

pop_path = "/opt/homebrew/Cellar/poppler/24.04.0_1/bin"
def pdf_to_images(pdf_path, dpi=500, poppler_path=pop_path):
    return convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)
