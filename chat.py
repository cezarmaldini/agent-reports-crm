# test_api.py
import requests

url = "http://127.0.0.1:8000/ask"

payload = {"query": "Quais os principais canais de contato com os leads?"}

response = requests.post(url, json=payload)

print("Status:", response.status_code)
print("Resposta:", response.json()['answer'])