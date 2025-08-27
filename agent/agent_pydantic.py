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

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do modelo LLM
llm = os.getenv("LLM_MODEL", "gpt-4o-mini")
model = OpenAIModel(llm)

# Dependências do agente
@dataclass
class CRMAgentDeps:
    supabase: Client
    openai_client: AsyncOpenAI

SYSTEM_PROMPT = """
Você é um especialista em análise de relatórios CRM.
Sua função é:
- Interpretar dados de relatórios mensais de CRM (negociações, vendas, tarefas, funil, motivos de perda, metas etc.)
- Gerar insights estratégicos
- Identificar gargalos no processo comercial
- Sugerir oportunidades de melhoria e recomendações práticas

Use sempre os relatórios armazenados no Supabase como base para sua resposta.
Se não encontrar informação suficiente, seja honesto e diga isso.
"""

# Criar o agente
crm_expert_agent = Agent(
    model,
    system_prompt=SYSTEM_PROMPT,
    deps_type=CRMAgentDeps,
    retries=2
)

# Gerar os embeddings de consultas
def get_embedding(text: str) -> List[float]:
    try:
        EMBED_MODEL_ID = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
        embedding_model = TextEmbedding(EMBED_MODEL_ID)
        embeddings = list(embedding_model.passage_embed([text]))
        return embeddings[0].tolist()
    except Exception as e:
        print(f"Erro ao gerar embedding: {e}")
        return [0] * 768

# Ferramenta que executa o RAG
@crm_expert_agent.tool
async def retrieve_relevant_reports(ctx: RunContext[CRMAgentDeps], user_query: str) -> str:
    """
    Recupera os trechos mais relevantes de relatórios CRM para responder a uma query.
    """
    try:
        # Gerar embedding da query
        query_embedding = get_embedding(user_query)

        # Buscar no Supabase os chunks mais relevantes
        result = ctx.deps.supabase.rpc(
            "match_reports_crm",
            {
                "query_embedding": query_embedding,
                "match_count": 5
            }
        ).execute()

        if not result.data:
            return "Nenhum dado relevante encontrado."

        # Formatar chunks encontrados
        context = []
        for doc in result.data:
            chunk = f"""
# {doc['metadata']['source']} - Chunk {doc['metadata']['chunk_index']}

{doc['content']}
"""
            context.append(chunk)

        return "\n\n---\n\n".join(context)

    except Exception as e:
        print(f"Erro ao buscar relatórios: {e}")
        return f"Erro: {str(e)}"