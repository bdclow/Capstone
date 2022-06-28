from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from tqdm import tqdm
import os

FOLDER_ID="13Rpxaog1CcxfLoD3VjrT_d58Oc7QEIFX"

def download_data():
    google_auth = GoogleAuth()
    google_auth.LocalWebserverAuth()

    drive = GoogleDrive(google_auth)
    file_list = drive.ListFile({'q': f"'{FOLDER_ID}' in parents and trashed=false", 'includeItemsFromAllDrives': True}).GetList()
    print("Downloading files from Google Drive...")
    os.mkdir('data')
    for file in tqdm(file_list):
        if file['mimeType'] == 'text/csv':
            file.GetContentFile(f"data/{file['title']}")

download_data()
