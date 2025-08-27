from __future__ import annotations as _annotations
from dataclasses import dataclass
from dotenv import load_dotenv
import os
from typing import List

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncOpenAI

from clients import new_supabase_client

load_dotenv()

llm = os.getenv('LLM_MODEL', 'gpt-4o-mini')
model = OpenAIModel(llm)

# Dependências do agente
class CRMAgentDeps:
    supabase: 
    openai_client: AsyncOpenAI

system_prompt = """
Você é um especialista em análise de relatórios CRM.
Sua função é:
- Interpretar dados de relatórios mensais de CRM (negociações, vendas, tarefas, funil, motivos de perda, metas etc.)
- Gerar insights estratégicos
- Identificar gargalos no processo comercial
- Sugerir oportunidades de melhoria e recomendações práticas

Use sempre os relatórios armazenados no Supabase como base para sua resposta.
Se não encontrar informação suficiente, seja honesto e diga isso.
"""

crm_expert_agent = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=CRMAgentDeps,
    retries=2

async def get_embedding(text: str, openai_client: AsyncOpenAI) -> List[float]:
    try:
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Erro ao gerar embedding: {e}")
        return [0] * 1536

# Ferramenta RAG: busca relatórios relevantes
@crm_expert_agent.tool
async def retrieve_relevant_reports(ctx: RunContext[CRMAgentDeps], user_query: str) -> str:
    """
    Recupera os trechos mais relevantes de relatórios CRM para responder a uma query.
    """
    try:
        # Gerar embedding da pergunta
        query_embedding = await get_embedding(user_query, ctx.deps.openai_client)

        # Buscar no Supabase os chunks mais relevantes
        result = ctx.deps.supabase.rpc(
            'match_site_pages',  # Função de busca vetorial criada no banco
            {
                'query_embedding': query_embedding,
                'match_count': 5,
                'filter': {'source': 'crm_reports'}  # <-- ajuste para seu caso
            }
        ).execute()

        if not result.data:
            return "Nenhum relatório relevante encontrado."

        # Formatar chunks
        formatted_chunks = []
        for doc in result.data:
            chunk_text = f"""
# {doc['metadata']['source']} - Chunk {doc['metadata']['chunk_index']}

{doc['content']}
"""
            formatted_chunks.append(chunk_text)

        return "\n\n---\n\n".join(formatted_chunks)