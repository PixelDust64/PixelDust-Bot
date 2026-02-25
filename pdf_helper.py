import pypdf
from pdf2image import convert_from_path
import os

def extrair_texto_pdf(pdf_path):
    texto_completo = ""
    try:
        reader = pypdf.PdfReader(pdf_path)
        for page in reader.pages:
            content = page.extract_text()
            if content:
                texto_completo += content + "\n"
    except Exception as e:
        print(f"Erro ao ler PDF: {e}")
    
    return texto_completo.strip()

def converter_pdf_em_imagem(pdf_path):
    # Converte apenas a primeira página para não sobrecarregar a GPU
    try:
        images = convert_from_path(pdf_path, first_page=1, last_page=1)
        if images:
            img_path = "pdf_page_one.jpg"
            images[0].save(img_path, 'JPEG')
            return img_path
    except Exception as e:
        print(f"Erro ao converter PDF: {e}")
    return None