import gradio as gr
import pandas as pd
import base64
import numpy as np
from config import POPLER_PATH
from execution_handler import handle_document
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts

# === Tema ===
theme = Base(
    primary_hue=colors.gray,
    font=fonts.GoogleFont("Helvetica Neue")
).set(
    body_background_fill="#ffffff",
    body_text_color="#111111",
    block_background_fill="#ffffff",
    block_border_color="#e0e0e0",
    block_shadow="0px 2px 6px rgba(0, 0, 0, 0.06)"
)

# === PDF inline gösterimi ===
def render_pdf_view(pdf_file):
    if not pdf_file:
        return ""
    with open(pdf_file, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')

    return f"""
    <iframe
        src="data:application/pdf;base64,{base64_pdf}"
        width="100%" height="600px"
        style="border: 1px solid #ccc; border-radius: 8px;">
    </iframe>
    """

# === Alanları güvenli şekilde çekmek için yardımcı ===
def safe_get(data, key, index=0):
    val = data.get(key)
    if val and isinstance(val, (list, tuple)) and len(val) > index:
        return val[index]
    return ""

# === Gradio üzerinden çağrılan asıl işlev ===
def extract_fields_from_pdf(pdf_file):
    extracted_data, product_table = handle_document(pdf_file, POPLER_PATH)
    return (
        safe_get(extracted_data, "establishment_code", 2),
        safe_get(extracted_data, "certificate_number", 2),
        safe_get(extracted_data, "validity_date", 1),
        extracted_data.get("revision_date", "") or "",
        extracted_data.get("certificate_type", "") or "",
        extracted_data.get("company_name", "") or "",
        product_table
    )

# === Arayüz ===
with gr.Blocks(theme=theme) as demo:
    gr.Markdown("## 🍃 İyi Tarım Sertifikası Görüntüleyici")

    with gr.Row():
        with gr.Column(scale=5):
            pdf_input = gr.File(label="📄 PDF Yükle", file_types=[".pdf"], interactive=True)
            pdf_view = gr.HTML(label="PDF Önizleme")
            run_button = gr.Button("🚀 Çıkarımları Başlat", variant="primary")

        with gr.Column(scale=5):
            code = gr.Textbox(label="Kuruluş Kodu", interactive=False)
            cert = gr.Textbox(label="Sertifika Numarası", interactive=False)
            date = gr.Textbox(label="Geçerlilik Tarihi", interactive=False)
            revision_date = gr.Textbox(label="Revizyon No ve Tarihi", interactive=False)
            cert_type = gr.Textbox(label="Sertifika Tipi", interactive=False)
            company = gr.Textbox(label="Firma İsmi", interactive=False)
            product_table = gr.Dataframe(label="📦 Ürün Detayları", wrap=True)

    # PDF yüklenince inline göster
    pdf_input.change(fn=render_pdf_view, inputs=[pdf_input], outputs=[pdf_view])

    # Butonla çıkarım başlat
    run_button.click(
        fn=extract_fields_from_pdf,
        inputs=[pdf_input],
        outputs=[code, cert, date,revision_date, cert_type, company, product_table]
    )

demo.launch()
