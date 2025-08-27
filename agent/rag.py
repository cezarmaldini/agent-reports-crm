import os
from typing import List, Dict, Any, Tuple
from fastembed import TextEmbedding
from clients import new_supabase_client

EMBED_MODEL_ID = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

_embedder = TextEmbedding(EMBED_MODEL_ID)
_supabase = new_supabase_client()

def _embed(text: str) -> List[float]:
    return list(_embedder.passage_embed([text]))[0].tolist()

def retrieve(query: str, k: int = 3) -> List[Dict[str, Any]]:
    vec = _embed(query)
    res = _supabase.rpc("match_documents_propostas", {"query_embedding": vec, "match_count": k}).execute()
    return res.data or []

def make_inference(query: str, llm_client, k: int = 3,
                   model_name: str = "llama-3.3-70b-versatile",
                   max_chars: int = 255) -> Tuple[str, List[Dict[str, Any]]]:
    
    matches = retrieve(query, k=k)
    
    docs_text = "\n\n".join(
        [f"Documento {i+1} (fonte: { (m.get('metadata') or {}).get('source','desconhecida') }): {m['content']}"
         for i, m in enumerate(matches)]
    )

    prompt = (
        f"Responda em PT-BR, de forma simples, usando no máximo {max_chars} caracteres, "
        f"**apenas** com base nos documentos abaixo. Se não encontrar, diga: "
        f"\"Não encontrei nos documentos\".\n\n"
        f"Documentos:\n{docs_text}\n\n"
        f"Pergunta: {query}"
    )

    chat = llm_client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "Você é um assistente útil e conciso."},
            {"role": "user", "content": prompt},
        ],
    )
    answer = chat.choices[0].message.content
    return answer, matches
