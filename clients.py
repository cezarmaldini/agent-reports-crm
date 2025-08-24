import os
from dotenv import load_dotenv
import requests

load_dotenv()

# Autenticação MicrosoftGraph
def get_access_token():
    TENANT_ID = os.getenv('TENANT_ID')
    CLIENT_ID = os.getenv('CLIENT_ID')
    CLIENT_SECRET = os.getenv('CLIENT_SECRET')

    token_url = f'https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token'

    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'scope': 'https://graph.microsoft.com/.default'
    }

    response = requests.post(token_url, data=data)
    response_json = response.json()

    if "access_token" not in response_json:
        raise Exception(f"Erro ao obter token: {response_json}")

    access_token = response_json["access_token"]
    return access_token

# Client Supabase
