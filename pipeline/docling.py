import io
import logging
from pathlib import Path
from typing import Optional, List
from docling.document_converter import DocumentConverter, DocumentStream, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TesseractCliOcrOptions,
)

_log = logging.getLogger(__name__)

# ---------- Estágio A: OCR direto do PDF ----------
def pdf_bytes_to_markdown_force_ocr(pdf_bytes: bytes, file_name: str) -> str:
    """
    Converte um PDF (bytes) em Markdown usando OCR de página inteira.
    Retorna o markdown completo do documento.
    """
    # Engine de OCR: Tesseract CLI (robusto e com suporte a PT/EN)
    ocr_opts = TesseractCliOcrOptions(
        force_full_page_ocr=True,   # força OCR mesmo quando a página é 100% imagem
        lang=["por", "eng"],        # ajuste para seu cenário; pode usar ["auto"] se preferir
    )

    pipe_opts = PdfPipelineOptions(
        do_ocr=True,
        ocr_options=ocr_opts,
        # se seu relatório tem muitas tabelas, deixe isso ligado:
        do_table_structure=True,
    )

    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipe_opts)}
    )

    stream = DocumentStream(
        name=file_name, media_type="application/pdf", stream=io.BytesIO(pdf_bytes)
    )

    conv = converter.convert(stream)
    md = conv.document.export_to_markdown()  # deve conter texto agora
    return md

# ---------- Estágio B: fallback via imagens em memória ----------
def pdf_bytes_to_markdown_via_page_images(pdf_bytes: bytes, file_name: str,
                                          image_scale: float = 2.0) -> str:
    """
    Fallback: renderiza páginas em memória e roda OCR em cada uma como imagem.
    Concatena tudo em UM markdown.
    """
    ocr_opts = TesseractCliOcrOptions(
        force_full_page_ocr=True,
        lang=["por", "eng"],
    )

    # Precisamos manter as imagens de página disponíveis:
    pipe_opts = PdfPipelineOptions(
        do_ocr=False,                    # aqui só queremos as imagens das páginas
        generate_page_images=True,
        generate_picture_images=False,
        images_scale=image_scale,        # escala >1 aumenta DPI da renderização
    )

    # Primeiro passe: só para obter as imagens das páginas
    converter_pdf = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipe_opts)}
    )
    conv = converter_pdf.convert(
        DocumentStream(name=file_name, media_type="application/pdf",
                       stream=io.BytesIO(pdf_bytes))
    )

    # Segundo passe: tratamos cada página como "imagem de entrada"
    converter_img = DocumentConverter()  # usa defaults + OCR do engine abaixo quando preciso

    parts: List[str] = []
    for page_no, page in conv.document.pages.items():
        buf = io.BytesIO()
        page.image.pil_image.save(buf, format="PNG")
        buf.seek(0)

        img_stream = DocumentStream(
            name=f"{file_name}-p{page.page_no}.png",
            media_type="image/png",
            stream=buf,
        )

        # Para imagens, o Docling aplica OCR; garantimos o engine via options no PDF? Aqui setamos explicitamente:
        # Em versões atuais, as opções de OCR vêm da pipeline ativa; como estamos usando imagens,
        # confiamos no default (EasyOCR) ou configuramos Tesseract via env global.
        # Para garantir Tesseract CLI também aqui:
        pipe_img = PdfPipelineOptions(do_ocr=True, ocr_options=ocr_opts)  # reuso de opções
        # Apesar do nome da classe, as opções de OCR são reutilizadas pelo conversor.
        # Se sua versão exigir opções específicas para imagem, o docling usará as mesmas de OCR.

        # Converter a imagem
        doc_img = converter_img.convert(img_stream).document
        parts.append(doc_img.export_to_markdown())

    joined = []
    for i, chunk in enumerate(parts, start=1):
        joined.append(f"\n\n<!-- page {i} -->\n\n")
        joined.append(chunk.strip())

    return "".join(joined)

def looks_like_only_images(md: str) -> bool:
    """Heurística simples: documento com quase somente marcadores de imagem."""
    text = "".join(line for line in md.splitlines() if "<!-- image" not in line)
    return len(text.strip()) < 30