import io
import os.path
import pickle

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

SCOPES = ['https://www.googleapis.com/auth/drive']
API_SERVICE_NAME = 'drive'
API_VERSION = 'v3'

UPLOAD_ID = '1gmDCNpGwsA7piGZF4aFBUmPPP949hYGO'  # id of the folder of google drive where the files will be saved


def get_authenticated_service():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.isfile('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return build('drive', 'v3', credentials=creds)


def upload_file(service, filename, filedata):
    results = service.files().list(
        q=(f"parents in '{UPLOAD_ID}' and name='{filename[:3]}'"
           " and mimeType='application/vnd.google-apps.folder'"),
        pageSize=1,
        fields='files(id)').execute()
    folder = None
    if len(results['files']):
        folder = results['files'][0]
    if not folder:  # create folder
        file_metadata = {
            'name': filename[:3],
            'parents': [UPLOAD_ID],
            'mimeType': 'application/vnd.google-apps.folder'
        }

        folder = service.files().create(body=file_metadata,
                                        fields='id').execute()
    file_metadata = {'name': filename,
                     'parents': [folder['id']]}
    media = MediaIoBaseUpload(io.BytesIO(filedata),
                              mimetype='application/octet-stream', resumable=False)
    r = service.files().create(body=file_metadata,  # upload file
                               media_body=media,
                               fields='id').execute()
    if not r.get('id'):
        raise RuntimeError('Error uploading file!')


def download_file(service, filename):
    results = service.files().list(
        q=(f"parents in '{UPLOAD_ID}' and name='{filename[:3]}'"
           " and mimeType='application/vnd.google-apps.folder'"),
        pageSize=1,
        fields='files(id)').execute()
    folder_id = results['files'][0]['id']

    results = service.files().list(
        q=f"parents in '{folder_id}' and name='{filename}'",
        pageSize=1,
        fields='files(id)').execute()
    file_id = results['files'][0]['id']
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    return fh.getbuffer()
