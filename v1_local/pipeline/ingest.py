import os
import uuid
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer
from fastembed import TextEmbedding

from clients import new_supabase_client

from dotenv import load_dotenv

load_dotenv()

def list_files(folder: str) -> List[str]:
    files = [
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith('.md')
    ]
    files.sort()
    return files

def convert_doc(file_path: str):

    converter = DocumentConverter()
    result = converter.convert(file_path)
    return result.document

def create_document_chunks(document, embed_model_id: str, max_tokens: int):
    
    tokenizer = AutoTokenizer.from_pretrained(embed_model_id)

    chunker = HybridChunker(
        tokenizer=tokenizer,
        max_tokens=max_tokens,
        merge_peers=True
    )

    chunk_iter = chunker.chunk(dl_doc=document)
    return list(chunk_iter)

def create_embeddings(chunks: List[Dict[str, Any]], model_name: str):
    model = TextEmbedding(model_name)
    texts = [chunk.text for chunk in chunks]
    embeddings = list(model.passage_embed(texts))
    return embeddings

def build_records(file_name: str, chunks: List[Dict[str, Any]], embeddings: List[Any]):
    records = []
    for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        record = {
            "id": str(uuid.uuid4()),
            "content": chunk.text,
            "metadata": {
                "source": file_name,
                "chunk_index": idx
            },
            "embedding": emb.tolist() if hasattr(emb, "tolist") else emb
        }
        records.append(record)
    return records

def insert_records(records: List[Dict[str, Any]], table_name: str = "reports_crm"):
    supabase = new_supabase_client()
    result = supabase.table(table_name).insert(records).execute()
    return result

def ingest_files(folder: str, model_name: str, max_tokens: int = 768):
    files = list_files(folder)

    files_process = []

    for file in files:
        file_name = os.path.basename(file)
        files_process.append(file_name)

        doc = convert_doc(file)
        chunks = create_document_chunks(doc, model_name, max_tokens)
        embeddings = create_embeddings(chunks, model_name)
        records = build_records(file_name, chunks, embeddings)
        insert_records(records=records)

    return files_process

def run_ingest_all():

    FOLDER = 'markdown'
    EMBED_MODEL_ID = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'

    date_process = datetime.today().strftime('%Y-%m-%d')

    files = ingest_files(folder=FOLDER, model_name=EMBED_MODEL_ID)

    columns = ['file_name']

    df = pd.DataFrame(files, columns=columns)

    df['date_process'] = date_process

    df.to_csv('data/files_process.csv', index=False)

    return files