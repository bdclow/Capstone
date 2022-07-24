from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from tqdm import tqdm
import argparse
import os
from src import data_dir


def download_data(drive_folder_id, target_dir, force_redownload):
    '''
    Through Drive api download files if don't exist already
    '''
    google_auth = GoogleAuth()
    google_auth.LocalWebserverAuth()

    drive = GoogleDrive(google_auth)
    file_list = drive.ListFile({
        'q': f"'{drive_folder_id}' in parents and trashed=false", 
        'includeItemsFromAllDrives': True})\
        .GetList()

    print("Downloading files from Google Drive...")
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)

    # Get list of existing files in that directory
    existing_files = [dir_entry.name 
            for dir_entry in os.scandir(target_dir) 
            if dir_entry.is_file()]

    # Loop through CSV files, and download if needed
    for file in (prog_bar := tqdm(file_list, ncols=100)):
        if file['mimeType'] == 'text/csv': 
            if force_redownload or (file['title'] not in existing_files):
                destination = os.path.join(target_dir, file['title'])
                prog_bar.set_description(f"Downloading {file['title']}") 
                file.GetContentFile(destination)

def main():
    parser = argparse.ArgumentParser(
            allow_abbrev=True,
            description='Download project data files via Google Drive API')
    parser.add_argument('--target_dir')
    parser.add_argument('--drive_folder_id')
    parser.add_argument('--force', 
            action='store_true', 
            help="Whether to force redownload all, defaults to only downloading files that don't exist")

    args = parser.parse_args()
    if args.drive_folder_id:
        drive_folder_id = args.drive_folder_id
    else:
        drive_folder_id = "13Rpxaog1CcxfLoD3VjrT_d58Oc7QEIFX"

    if args.target_dir:
        target_dir = args.target_dir
    else:
        target_dir = data_dir

    download_data(
            drive_folder_id=drive_folder_id,
            target_dir=target_dir,
            force_redownload=args.force)

main()
