import io
from pathlib import Path
from shutil import which

from docling.document_converter import DocumentConverter, DocumentStream, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TesseractCliOcrOptions,  # use Tesseract CLI se disponível
    # Você pode alternar por EasyOCR/RapidOCR se preferir.
)

def pdf_bytes_to_markdown(pdf_bytes: bytes, file_name: str) -> str:
    """
    Converte um PDF (em bytes) para Markdown (string), com OCR habilitado.
    Não grava imagens nem páginas em disco.
    """
    pipeline_options = PdfPipelineOptions()

    # Habilita OCR (essencial para PDF imagem)
    pipeline_options.do_ocr = True

    # Se o Tesseract CLI estiver instalado, usa OCR forçado em página inteira
    # (para PDFs 100% escaneados). Caso não esteja, o Docling usa OCR padrão.
    if which("tesseract"):
        pipeline_options.ocr_options = TesseractCliOcrOptions(force_full_page_ocr=True)

    # Não precisamos gerar imagens de página/figuras para o seu objetivo
    pipeline_options.generate_page_images = False
    pipeline_options.generate_picture_images = False

    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )

    doc_stream = DocumentStream(
        name=file_name,
        media_type="application/pdf",
        stream=io.BytesIO(pdf_bytes),
    )

    conv_res = converter.convert(doc_stream)

    # Exporta TODO o documento para Markdown (uma string) — inclui todas as páginas.
    # (Se quiser imagens embutidas em base64, use save_as_markdown(..., image_mode=...).
    md_text = conv_res.document.export_to_markdown()
    return md_text