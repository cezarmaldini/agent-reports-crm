from __future__ import annotations as _annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv
from typing import List

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncOpenAI
from fastembed.embedding import TextEmbedding
from supabase import Client

from prompts import SYSTEM_PROMPT

from clients import new_supabase_client

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do modelo LLM
llm = os.getenv("LLM_MODEL", "gpt-4o-mini")
model = OpenAIModel(llm)

# Modelo de embeddings
EMBED_MODEL_ID = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
embedding_model = TextEmbedding(EMBED_MODEL_ID)

# Dependências do agente
@dataclass
class CRMAgentDeps:
    supabase: Client
    openai_client: AsyncOpenAI

# Criar o agente
crm_expert_agent = Agent(
    model,
    system_prompt=SYSTEM_PROMPT,
    deps_type=CRMAgentDeps,
    retries=2
)

# Gerar os embeddings de consultas
def get_embedding(text: str, embedding_model_id: str) -> List[float]:
    try:
        embedding_model = TextEmbedding(embedding_model_id)
        embeddings = list(embedding_model.passage_embed([text]))
        return embeddings[0].tolist()
    except Exception as e:
        print(f"Erro ao gerar embedding: {e}")
        return [0] * 768

# Ferramenta que executa o RAG
@crm_expert_agent.tool
async def retrieve_relevant_reports(ctx: RunContext[CRMAgentDeps], user_query: str, embedding_model_id: str) -> str:
    """
    Recupera os trechos mais relevantes de relatórios CRM para responder a uma query.
    """
    try:
        # Gerar embedding da query
        query_embedding = get_embedding(user_query, embedding_model_id)

        # Buscar no Supabase os chunks mais relevantes
        result = ctx.deps.supabase.rpc(
            "match_reports_crm",
            {
                "query_embedding": query_embedding,
                "match_count": 5
            }
        ).execute()

        if not result.data:
            return "Nenhum relatório relevante encontrado."

        # Formatar chunks encontrados
        formatted_chunks = []
        for doc in result.data:
            chunk_text = f"""
# {doc['metadata']['source']} - Chunk {doc['metadata']['chunk_index']}

{doc['content']}
"""
            formatted_chunks.append(chunk_text)

        return "\n\n---\n\n".join(formatted_chunks)

    except Exception as e:
        print(f"Erro ao buscar relatórios: {e}")
        return f"Erro: {str(e)}"

# Inicialização das dependências (exemplo)
def init_deps() -> CRMAgentDeps:
    supabase_client = new_supabase_client()
    openai_client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return CRMAgentDeps(supabase=supabase_client, openai_client=openai_client)