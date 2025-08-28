from fastapi import FastAPI
from pydantic import BaseModel

import clients
from agent.agent_pydantic import crm_expert_agent, CRMAgentDeps

# Inicializar FastAPI
app = FastAPI(title="CRM Expert Agent API", version=0.1)

# Modelo para requisição
class QueryRequest(BaseModel):
    query: str

# Criar instâncias de dependências do agente
supabase = clients.new_supabase_client()

openai_client = clients.new_client_openai()

deps = CRMAgentDeps(supabase=supabase, openai_client=openai_client)

@app.post("/ask")
async def ask_agent(request: QueryRequest):
    try:
        # Rodar agente passando a query e as dependências
        result = await crm_expert_agent.run(request.query, deps=deps)
        return {"answer": result.output}
    except Exception as e:
        return {"error": str(e)}