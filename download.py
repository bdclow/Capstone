from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from tqdm import tqdm
import argparse
import os


def download_data(drive_folder_id, target_dir, force_redownload):
    '''
    Through drive api download files if don't exist already
    '''
    google_auth = GoogleAuth()
    google_auth.LocalWebserverAuth()

    drive = GoogleDrive(google_auth)
    file_list = drive.ListFile({'q': f"'{drive_folder_id}' in parents and trashed=false", 'includeItemsFromAllDrives': True}).GetList()

    print("Downloading files from Google Drive...")
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)

    existing_files = os.scandir(target_dir)
    for file in tqdm(file_list):
        if file['mimeType'] == 'text/csv': 
            if not force_redownload and (file not in existing_files):
                file.GetContentFile(f"data/{file['title']}")

def main():
    parser = argparse.ArgumentParser(
            allow_abbrev=True,
            description='Download project data files via Google drive api')
    parser.add_argument('--target_dir')
    parser.add_argument('--drive_folder_id')
    parser.add_argument('--force', 
            action='store_false', 
            help='Whether to force redownload all, defaults to not redownloading')

    args = parser.parse_args()
    if args.drive_folder_id:
        drive_folder_id = args.drive_folder_id
    else:
        drive_folder_id = "13Rpxaog1CcxfLoD3VjrT_d58Oc7QEIFX"

    if args.target_dir:
        target_dir = args.target_dir
    else:
        target_dir = "data/"

    download_data(
            drive_folder_id=drive_folder_id,
            target_dir=target_dir,
            force_redownload=args.force)

main()
