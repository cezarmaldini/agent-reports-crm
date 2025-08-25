import os
import uuid
import json
import logging
from typing import List, Dict, Any, Iterable

from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from fastembed import TextEmbedding

import clients

# ----------------------------
# Configurações
# ----------------------------
MARKDOWN_DIR = "markdown"
TABLE_NAME = "documents"      # ajuste se seu nome for diferente
CHUNKER_TOKENIZER = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
EMBEDDING_DIM = 768
BATCH_SIZE = 128              # ajuste conforme memória / throughput
# ----------------------------

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
    return converter.convert(file_path)

# 3) Produzir chunks (iterable)
def chunk_document(dl_document, chunker: HybridChunker) -> Iterable:
    """
    Recebe o objeto dl_document e devolve iterator de chunks.
    Cada chunk deve ter .text
    """
    return chunker.chunk(dl_doc=dl_document)

# 4) Embedding em lote
def embed_texts(texts: List[str], embedder: TextEmbedding) -> List[List[float]]:
    """
    Gera embeddings para uma lista de textos. Retorna lista de vetores (listas de floats).
    """
    if not texts:
        return []
    embs = embedder.passage_embed(texts)  # pode retornar np.array, lista, etc.
    # Normalize para lista de listas de floats
    vectors = []
    for v in embs:
        try:
            vectors.append(v.tolist())
        except Exception:
            # já pode ser lista
            vectors.append(list(v))
    return vectors

# 5) Montar registros para inserir no Supabase
def build_records(file_path: str, chunks: List[Any], embeddings: List[List[float]]) -> List[Dict[str, Any]]:
    """
    Produz uma lista de dicts: {'id':..., 'content':..., 'metadata': {...}, 'embedding': [...]}
    metadata é um dict (supabase-py lida com json/dict)
    """
    records = []
    for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
        rec = {
            "id": str(uuid.uuid4()),
            "content": chunk.text if hasattr(chunk, "text") else str(chunk),
            "metadata": {
                "source": file_path,
                "chunk_index": idx,
            },
            "embedding": emb
        }
        records.append(rec)
    return records

# 6) Inserir no Supabase em batches
def insert_records_supabase(supabase_client, table_name: str, records: List[Dict[str, Any]], batch_size: int = 128):
    """
    Insere em batches. Uso esperado: supabase_client.table(table_name).insert(batch).execute()
    Ajuste se seu client for diferente.
    """
    total = len(records)
    logger.info(f"Inserindo {total} registros em batches de {batch_size} na tabela '{table_name}'")
    for i in range(0, total, batch_size):
        batch = records[i:i + batch_size]
        try:
            # supabase-py typical pattern
            resp = supabase_client.table(table_name).insert(batch).execute()
            # Verifique resp se quiser
            logger.info(f"Batch {i//batch_size + 1} inserido: {len(batch)} registros")
        except Exception as e:
            logger.error(f"Erro inserindo batch {i//batch_size + 1}: {e}")
            # fallback: tentar inserir linha a linha para isolar problema
            for rec in batch:
                try:
                    supabase_client.table(table_name).insert(rec).execute()
                except Exception as e2:
                    logger.exception(f"Falha ao inserir registro {rec.get('id')}: {e2}")

# 7) Pipeline por arquivo (junta as funções acima)
def ingest_file_to_supabase(file_path: str,
                            converter: DocumentConverter,
                            chunker: HybridChunker,
                            embedder: TextEmbedding,
                            supabase_client,
                            table_name: str,
                            batch_size: int = 128):
    doc = convert_file_to_doc(file_path, converter)
    # doc.document é o que o chunker espera (como no seu exemplo de referência)
    chunk_iter = chunk_document(doc.document, chunker)
    chunks = list(chunk_iter)  # materializa para poder batchar embeddings
    texts = [c.text for c in chunks]
    # gerar embeddings por lotes internos para não estourar memória
    records = []
    for j in range(0, len(texts), batch_size):
        texts_batch = texts[j:j+batch_size]
        emb_batch = embed_texts(texts_batch, embedder)
        chunk_slice = chunks[j:j+batch_size]
        recs = build_records(file_path, chunk_slice, emb_batch)
        records.extend(recs)

    # inserir todos os registros do arquivo
    insert_records_supabase(supabase_client, table_name, records, batch_size=batch_size)
    logger.info(f"Ingestão concluída do arquivo {file_path}: {len(records)} chunks inseridos")
    return len(records)

# 8) Orquestrador principal (processa todos os MD)
def run_ingest_all(markdown_dir: str = MARKDOWN_DIR,
                   table_name: str = TABLE_NAME,
                   batch_size: int = BATCH_SIZE,
                   chunker_tokenizer: str = CHUNKER_TOKENIZER):
    # 1) clientes
    supabase_client = clients.new_supabase_client()

    # 2) modelos / ferramentas
    converter = DocumentConverter()
    chunker = HybridChunker(tokenizer=chunker_tokenizer, max_tokens=EMBEDDING_DIM, merge_peers=True)
    embedder = TextEmbedding(model_name=chunker_tokenizer)

    files = list_markdown_files(markdown_dir)
    logger.info(f"{len(files)} arquivo(s) markdown encontrados em '{markdown_dir}'")

    total_chunks = 0
    for f in files:
        try:
            n = ingest_file_to_supabase(f, converter, chunker, embedder, supabase_client, table_name, batch_size)
            total_chunks += n
        except Exception as e:
            logger.exception(f"Erro processando arquivo {f}: {e}")

    logger.info(f"Ingest total concluído. {total_chunks} chunks inseridos.")
    return total_chunks

# run from command line
if __name__ == "__main__":
    run_ingest_all()