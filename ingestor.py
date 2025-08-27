import os
import io
import uuid
import requests
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

from docling.document_converter import DocumentConverter, DocumentStream
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from transformers import AutoTokenizer
from fastembed import TextEmbedding

from clients import new_supabase_client, get_access_token

from dotenv import load_dotenv

load_dotenv()

def extract_files_sharepoint(site_name, folder_path):
    access_token = get_access_token()

    response_site = requests.get(
        f'https://graph.microsoft.com/v1.0/sites/taticogestao.sharepoint.com:/sites/{site_name}',
        headers={
            'Authorization': f'Bearer {access_token}'
        }
    )

    site_id = response_site.json().get("id")

    response_drive = requests.get(
        f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    drive_id = response_drive.json()['id']

    response_files = requests.get(
        f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{folder_path}:/children",
        headers={"Authorization": f"Bearer {access_token}"}  
    )

    items = response_files.json().get("value", [])
    folders = [item for item in items if "folder" in item]

    pdf_files = []

    # Para cada pasta (ano), lista os arquivos
    for folder in folders:
        folder_name = folder["name"]
        path = f"{folder_path}/{folder_name}"
        
        response_sub = requests.get(
            f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{path}:/children",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        files_in_folder = response_sub.json().get("value", [])

        for file in files_in_folder:
            file_name = file["name"]
            download_url = file.get("@microsoft.graph.downloadUrl")
            if not download_url:
                continue

            file_resp = requests.get(download_url)
            if file_resp.status_code == 200:
                pdf_files.append({
                    "folder": folder_name,
                    "file_name": file_name,
                    "content": file_resp.content 
                })
            else:
                print(f"Erro ao baixar {file_name}: {file_resp.status_code}")

    return pdf_files


def convert_doc(pdf_bytes):
    converter = DocumentConverter()

    stream = io.BytesIO(pdf_bytes)

    doc_stream = DocumentStream(stream=stream, file_type='pdf', name='temp.pdf')

    result = converter.convert(doc_stream)
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

def ingest_files(site_name: str, folder_path: str, model_name: str, max_tokens: int):
    files = extract_files_sharepoint(site_name, folder_path)

    files_process = []

    for file in files:
        file_name = file['file_name']
        file_content = file['content']
        files_process.append(file_name)

        doc = convert_doc(file_content)
        chunks = create_document_chunks(doc, model_name, max_tokens)
        embeddings = create_embeddings(chunks, model_name)
        records = build_records(file_name, chunks, embeddings)
        insert_records(records=records)

    return files_process

def main():

    SITE_SHAREPOINT = os.getenv('SITE_SHAREPOINT')
    FOLDER_SHAREPOINT = os.getenv('FOLDER_SHAREPOINT')
    EMBED_MODEL_ID = 'sentence-transformers/paraphrase-multilingual-mpnet-base-v2'
    MAX_TOKENS = 768

    date_process = datetime.today().strftime('%Y-%m-%d')

    files = ingest_files(site_name=SITE_SHAREPOINT, folder_path=FOLDER_SHAREPOINT, model_name=EMBED_MODEL_ID, max_tokens=MAX_TOKENS)

    columns = ['file_name']

    df = pd.DataFrame(files, columns=columns)

    df['date_process'] = date_process

    df.to_csv('data/files_process.csv', index=False)

    return files

if __name__ == '__main__':
    main()