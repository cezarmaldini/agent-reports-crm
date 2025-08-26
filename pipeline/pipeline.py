import os
from pathlib import Path
from dotenv import load_dotenv

from pipeline import extract, transform, ingest

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
    ingest.run_ingest_all()
    
    print('Processo concluído!')

if __name__ == "__main__":
    main()