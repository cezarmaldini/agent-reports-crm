import os
import uuid
import json
import logging
from typing import List, Dict, Any, Iterable

from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from fastembed import TextEmbedding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ingest_supabase")

# 1) Listar arquivos markdown
def list_markdown_files(folder: str) -> List[str]:
    files = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(".md")
    ]
    files.sort()
    return files

# 2) Ler/converter arquivo com docling
def convert_file_to_doc(file_path: str, converter: DocumentConverter):
    """
    Retorna o objeto que converter.convert(file_path) devolve.
    O chunker usado posteriormente vai esperar doc.document.
    """
    logger.debug(f"Convertendo: {file_path}")
    return converter.convert(file_path)

if __name__ == '__main__':
    files = list_markdown_files(folder='markdown')

    print(files)