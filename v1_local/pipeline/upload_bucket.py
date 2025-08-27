import re
import unicodedata
from datetime import datetime

from clients import new_supabase_client

def sanitize_filename(filename: str) -> str:
    # Remove acentos
    nfkd = unicodedata.normalize("NFKD", filename)
    no_accent = "".join([c for c in nfkd if not unicodedata.combining(c)])

    # Substitui caracteres inválidos por "_"
    sanitized = re.sub(r'[^a-zA-Z0-9._\- ()]', "_", no_accent)

    return sanitized

def upload_files_to_bucket(file_name: str, markdown_content: str, bucket_name: str = "reports_crm"):
    try:
        folder = datetime.today().strftime("%Y%m%d")

        path = f'{folder}/{file_name}'

        supabase = new_supabase_client()

        supabase.storage.from_(bucket_name).upload(path, markdown_content.encode('utf-8'))
    
    except Exception as e:
        print(f'Erro: {e}')

        return None
