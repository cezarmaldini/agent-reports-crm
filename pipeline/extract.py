import os
import requests
from dotenv import load_dotenv

import clients

load_dotenv()

def ingest_files_sharepoint(site_name, folder_path):
    access_token = clients.get_access_token()

    response_site = requests.get(
        f'https://graph.microsoft.com/v1.0/sites/taticogestao.sharepoint.com:/sites/{site_name}',
        headers={
            'Authorization': f'Bearer {access_token}'
        }
    )

    site_id = response_site.json().get("id")

    response_drive = requests.get(
        f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    drive_id = response_drive.json()['id']

    response_files = requests.get(
        f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{folder_path}:/children",
        headers={"Authorization": f"Bearer {access_token}"}  
    )

    items = response_files.json().get("value", [])
    folders = [item for item in items if "folder" in item]

    pdf_files = []

    # Para cada pasta (ano), lista os arquivos
    for folder in folders:
        folder_name = folder["name"]
        path = f"{folder_path}/{folder_name}"
        
        response_sub = requests.get(
            f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{path}:/children",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        files_in_folder = response_sub.json().get("value", [])

        for file in files_in_folder:
            file_name = file["name"]
            download_url = file.get("@microsoft.graph.downloadUrl")
            if not download_url:
                continue

            file_resp = requests.get(download_url)
            if file_resp.status_code == 200:
                pdf_files.append({
                    "folder": folder_name,
                    "file_name": file_name,
                    "content": file_resp.content 
                })
            else:
                print(f"Erro ao baixar {file_name}: {file_resp.status_code}")

    return pdf_files[60:62]