import os.path
import io
import time
import sys

# THIRD PARTY IMPORTS -
import PyPDF2
from PIL import Image
from google import genai
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
from dotenv import load_dotenv

load_dotenv()
# _______________________________________________________________________
#                          1. CONFIGURATION
# _______________________________________________________________________

# API KEYS & ID
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("API Key not found!")

TARGET_FOLDER_ID = "16KpzhwmD5ndJkTliTwjE9NsVE60HRWwF"

# SETTINGS
CATEGORIES = ["Finance", "HR", "Projects", "Personal", "Marketing", "Academics"]
SCOPES = ['https://www.googleapis.com/auth/drive']
MODEL_NAME = 'gemini-2.5-flash'

# OPERATION MODE
# True = Simulation (Safe Mode)
# False = Real Mode (Actually moves files)
DRY_RUN = False 

# _______________________________________________________________________
#                           2. HELPER FUNCTIONS
# _______________________________________________________________________

def authenticate_drive():
    """Authenticates the user with Google Drive API."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port = 0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def read_file_content(service, file_id, mime_type):
    """
    Downloads file content. 
    Returns TEXT string for Docs/PDFs or IMAGE object for JPG/PNG.
    """
    try:
        # CASE A - Images
        if 'image/' in mime_type:
            request = service.files().get_media(fileId = file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            fh.seek(0)
            return Image.open(fh)

        # CASE B - Google Docs
        elif mime_type == 'application/vnd.google-apps.document':
            request = service.files().export_media(fileId = file_id, mimeType='text/plain')
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            return fh.getvalue().decode('utf-8')[:2000]

        # CASE C - PDFs and Text
        elif 'pdf' in mime_type or 'text' in mime_type:
            request = service.files().get_media(fileId = file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            fh.seek(0)
            
            if 'pdf' in mime_type:
                try:
                    reader = PyPDF2.PdfReader(fh)
                    content = ""
                    for i in range(min(2, len(reader.pages))):
                        content += reader.pages[i].extract_text()
                    return content
                except:
                    return ""
            else:
                return fh.read().decode('utf-8')[:2000]

        return None # Unsupported type

    except Exception as e:
        print(f"Error reading content -> {e}")
        return None

def create_folder_if_not_exists(service, folder_name, parent_id):
    """Creates a category folder if it doesn't exist."""
    query = f"name = '{folder_name}' and '{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q = query, spaces = 'drive', fields = 'files(id, name)').execute()
    files = results.get('files', [])

    if files:
        return files[0]['id']
    else:
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parent_id]
        }
        file = service.files().create(body = file_metadata, fields = 'id').execute()
        print(f"Created new folder: {folder_name}")
        return file.get('id')

def move_file(service, file_id, new_parent_id, dry_run=False):
    """Moves the file to the new folder."""
    if dry_run:
        print(f"[DRY RUN] Would move file {file_id} to {new_parent_id}")
        return

    try:
        file = service.files().get(fileId = file_id, fields='parents').execute()
        previous_parents = ",".join(file.get('parents'))
        service.files().update(
            fileId = file_id,
            addParents = new_parent_id,
            removeParents = previous_parents,
            fields = 'id, parents'
        ).execute()
        print(f"[SUCCESS] File moved.")
    except HttpError as error:
        print(f"[ERROR] moving file: {error}")

def classify_file_with_content(filename, mime_type, content_data):
    """Uses Gemini to classify the file."""
    client = genai.Client(api_key = GEMINI_API_KEY)
    
    instruction = (
        f"I have a file named '{filename}' (Type: {mime_type}). "
        f"Categorize it into strictly one of these folders: {CATEGORIES}. "
        f"Reply ONLY with the category name. If unsure, reply 'Misc'."
    )
    
    try:
        # Multimodal (Image)
        if isinstance(content_data, Image.Image):
            response = client.models.generate_content(
                model = MODEL_NAME,
                contents = [content_data, instruction]
            )
        # Text
        else:
            if not content_data: 
                content_data = "No readable content."
            prompt = f"{instruction}\n\nFile Content Snippet:\n\"\"\"{content_data}\"\"\""
            response = client.models.generate_content(
                model = MODEL_NAME,
                contents = prompt
            )
        
        category = response.text.strip()
        if category not in CATEGORIES:
            return "Misc"
        return category

    except Exception as e:
        print(f"   [AI Error]: {e}")
        return "Misc"

# _______________________________________________________________________
#                            3. MAIN EXECUTION
# _______________________________________________________________________

def main():
    print("--- SMART GOOGLE DRIVE ORGANIZER ---")
    print("1. Authenticating...")
    service = authenticate_drive()
    print("   Authentication successful.")

    print(f"2. Scanning Folder: {TARGET_FOLDER_ID}")
    print(f"MODE: {'SAFE (Simulation)' if DRY_RUN else 'LIVE (Moving Files)'}")

    # List files
    query = f"'{TARGET_FOLDER_ID}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q = query, pageSize = 20, fields = "nextPageToken, files(id, name, mimeType)").execute()
    items = results.get('files', [])

    if not items:
        print('\nNo files found to organize.')
        return

    print(f"\nFound {len(items)} files. Starting process...\n")

    for item in items:
        name = item['name']
        file_id = item['id']
        mime = item['mimeType']
        
        print(f"Processing: {name}")
        
        # 1. Read Content
        print("...reading content...")
        content_snippet = read_file_content(service, file_id, mime)
        
        # 2. Classify (with Retry)
        category = "Misc"
        retries = 0
        while retries < 3:
            category = classify_file_with_content(name, mime, content_snippet)
            if category != "Misc":
                break
            break 
        
        print(f"AI Decision: {category}")
        
        # 3. Move File
        dest_folder_id = create_folder_if_not_exists(service, category, TARGET_FOLDER_ID)
        if dest_folder_id:
            move_file(service, file_id, dest_folder_id, dry_run = DRY_RUN)
        
        print("__" * 40)
        
        # 4. Rate Limit Pause
        print("Cooling down for 60 seconds (API limits)...")
        time.sleep(60)

if __name__ == '__main__':
    main()