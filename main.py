import os
from pathlib import Path
from dotenv import load_dotenv

from pipeline import extract, transform

load_dotenv()

def main():
    SITE_SHAREPOINT = os.getenv('SITE_SHAREPOINT')
    FOLDER_SHAREPOINT = os.getenv('FOLDER_SHAREPOINT')
    print('Buscando arquivos no sharepoint')
    files = extract.ingest_files_sharepoint(site_name=SITE_SHAREPOINT, folder_path=FOLDER_SHAREPOINT)
    
    print('Processando arquivos...')
    content = files['content']
    
    file_name = files['file_name']

    output_dir = Path("images")

    process = transform.process_pdf_in_memory(pdf_bytes=content, file_name=file_name, output_dir=output_dir)

    print('Processo concluído!')

if __name__ == "__main__":
    main()