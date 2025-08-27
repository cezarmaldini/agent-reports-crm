import os
from pathlib import Path
from dotenv import load_dotenv

from pipeline import extract, transform, ingest, upload_bucket

load_dotenv()

def main():
    SITE_SHAREPOINT = os.getenv('SITE_SHAREPOINT')
    FOLDER_SHAREPOINT = os.getenv('FOLDER_SHAREPOINT')

    print('Buscando arquivos no sharepoint...')
    files = extract.ingest_files_sharepoint(site_name=SITE_SHAREPOINT,folder_path=FOLDER_SHAREPOINT)

    print('Salvando imagens...')
    images = Path("images")
    images.mkdir(parents=True, exist_ok=True)

    for file in files:
        file_name = file['file_name']
        pdf_bytes = file['content']

        transform.process_pdf_in_memory(pdf_bytes=pdf_bytes, file_name=file_name, output_dir=images)
    
    print('Gerando arquivos markdowns...')
    transform.images_to_markdown(images_dir=images, output_dir='markdown')

    print('Salvando arquivos no VectorDB...')
    files_process = ingest.run_ingest_all()

    print('Upload dos arquivos no bucket...')
    for file_name in files_process:
        path = os.path.join('markdown', file_name)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            sanitized_name = upload_bucket.sanitize_filename(file_name)
            upload_bucket.upload_files_to_bucket(file_name=sanitized_name, markdown_content=content)

        except FileNotFoundError:
            print(f"❌ Arquivo não encontrado: {file_name}")
        except Exception as e:
            print(f"❌ Erro ao processar {file_name}: {e}")

    print('Processo concluído!')

if __name__ == "__main__":
    main()