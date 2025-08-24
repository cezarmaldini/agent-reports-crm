import os
from pathlib import Path
from dotenv import load_dotenv

from pipeline import extract, transform

load_dotenv()

def main():
    SITE_SHAREPOINT = os.getenv('SITE_SHAREPOINT')
    FOLDER_SHAREPOINT = os.getenv('FOLDER_SHAREPOINT')

    print('Buscando arquivos no sharepoint')
    files = extract.ingest_files_sharepoint(
        site_name=SITE_SHAREPOINT,
        folder_path=FOLDER_SHAREPOINT
    )

    print('Convertendo para Markdown (em memória)...')
    md_out_dir = Path("markdown")
    md_out_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        file_name = file['file_name']
        pdf_bytes = file['content']

        md_str = transform.pdf_bytes_to_markdown(pdf_bytes=pdf_bytes, file_name=file_name)

        out_path = md_out_dir / (Path(file_name).stem + ".md")
        out_path.write_text(md_str, encoding="utf-8")

    print('Processo concluído!')

if __name__ == "__main__":
    main()