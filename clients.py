import os
import requests
from supabase import create_client, Client
from openai import AsyncOpenAI
from dotenv import load_dotenv

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
def new_supabase_client():
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    
    supabase: Client = create_client(url, key)

    return supabase

# Cliente OpenAI
def new_client_openai():
    openai_api_key: str = os.environ.get('OPENAI_API_KEY')

    openai_client = AsyncOpenAI(api_key=openai_api_key)

    return openai_client