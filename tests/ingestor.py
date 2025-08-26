import os
from pipeline import ingest
from pipeline import upload_bucket

files_process = ingest.run_ingest_all()

for file_name in files_process:
    path = os.path.join('markdown', file_name)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()

        sanitized_name = upload_bucket.sanitize_filename(file_name)
        upload_bucket.upload_files_to_bucket(file_name=sanitized_name, markdown_content=content)

        print(f"✅ Arquivo enviado: {file_name}")

    except FileNotFoundError:
        print(f"❌ Arquivo não encontrado: {file_name}")
    except Exception as e:
        print(f"❌ Erro ao processar {file_name}: {e}")
