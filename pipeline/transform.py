import io
import logging
from pathlib import Path
from docling.document_converter import DocumentConverter, DocumentStream, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

def process_pdf_in_memory(pdf_bytes: bytes, file_name: str, output_dir: Path):
    """
    Converte e exporta imagens/markdown/HTML de um PDF em memória (bytes).
    """
    IMAGE_RESOLUTION_SCALE = 2.0
    _log = logging.getLogger(__name__)

    pipeline_options = PdfPipelineOptions()
    pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    doc_stream = DocumentStream(
        name=file_name,
        media_type="application/pdf",
        stream=io.BytesIO(pdf_bytes)
    )

    conv_res = doc_converter.convert(doc_stream)

    output_dir.mkdir(parents=True, exist_ok=True)
    doc_filename = Path(file_name).stem

    for page_no, page in conv_res.document.pages.items():
        page_no = page.page_no
        page_image_filename = output_dir / f"{doc_filename}-{page_no}.png"
        with page_image_filename.open("wb") as fp:
            page.image.pil_image.save(fp, format="PNG")