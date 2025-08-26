# exemplo com OpenAI; troque pelo seu provedor se quiser manter Llama 70B
import os
from dotenv import load_dotenv
from openai import OpenAI
from rag import make_inference

load_dotenv()

llm = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
resposta, fontes = make_inference("Faça um resumo do documento", llm_client=llm, k=3, model_name="gpt-4o-mini")

print("Resposta:", resposta)
for f in fontes:
    print("Fonte:", (f.get("metadata") or {}).get("source"), " | Similaridade:", round(f["similarity"], 3))
