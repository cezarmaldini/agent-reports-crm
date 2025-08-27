import asyncio
from agent.agent_pydantic import crm_expert_agent, init_deps

async def main():
    # Inicializar dependências
    deps = init_deps()

    # Pergunta de teste
    pergunta = "Qual o último mês registrado nos relatórios?"

    print("\n➡️ Pergunta do usuário:")
    print(pergunta)

    # Rodar o agente com a query
    resposta = await crm_expert_agent.run(pergunta, deps=deps)

    print("\n🤖 Resposta do agente:")
    print(resposta)

if __name__ == "__main__":
    asyncio.run(main())