""""
Interactions with Google Drive, Docs and related API.
"""

import os

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")


class GoogleDrive:
    def __init__(self, user):
        user_creds = user["oauth_credentials"]

        if not user_creds:
            raise ValueError("User does not have authentication details.")

        self.creds = Credentials(
            None,
            refresh_token=user_creds["refresh_token"],
            token_uri=user_creds["token_uri"],
            client_id=GOOGLE_CLIENT_ID,
            client_secret=GOOGLE_CLIENT_SECRET,
        )

    @property
    def files(self):
        if not hasattr(self, "_files"):
            self._files = build("drive", "v3", credentials=self.creds).files()

        return self._files

    @property
    def permissions(self):
        if not hasattr(self, "_permissions"):
            self._permissions = build(
                "drive", "v3", credentials=self.creds
            ).permissions()

        return self._permissions

    @property
    def docs(self):
        if not hasattr(self, "_docs"):
            self._docs = build("docs", "v1", credentials=self.creds).documents()

        return self._docs

    @property
    def sheets(self):
        if not hasattr(self, "_sheets"):
            self._sheets = build("sheets", "v4", credentials=self.creds).spreadsheets()

        return self._sheets

    def create_document(self, document_name):
        """
        Create an output document in users's Google Drive.

        :returns: Document's ID
        """

        body = {"title": document_name}
        file = self.docs.create(body=body, fields="documentId").execute()

        return file.get("documentId")

    def append_document_text(self, document_id, text):
        """
        Create an output document in users's Google Drive.

        :returns: Document's ID
        """

        requests = []
        requests.append(
            {"insertText": {"text": text, "endOfSegmentLocation": {"segmentId": ""}}}
        )

        body = {"requests": requests}
        results = self.docs.batchUpdate(documentId=document_id, body=body).execute()

        return results


    # use this to update the doc text styles
    def update_document_text_style(self, document_id, startI, endI, Style, fields):
        """
        Create an output document in users's Google Drive.

        :returns: Document's ID
        """

        requests = []
        requests.append(
            { 'updateTextStyle': { 'range': { 'startIndex': startI, 'endIndex':endI }, 'textStyle': Style, 'fields': fields } }
        )

        body = {"requests": requests}
        results = self.docs.batchUpdate(documentId=document_id, body=body).execute()

        return results

    def create_folder(self, folder_name, *, parent="root"):
        """
        Create a folder in the users's Google Drive.

        :returns: Folder's ID
        """

        body = {
            "name": folder_name,
            "mimeType": "application/vnd.google-apps.folder",
            "parents": [parent],
        }
        file = self.files.create(
            body=body, fields="id", supportsAllDrives=True
        ).execute()

        return file.get("id")

    def copy_document(self, document_id, new_document_name, *, parent=None):
        """
        Copies an existing document in the users's Google Drive.

        :returns: Document's ID
        """

        body = {"name": new_document_name}
        if parent:
            body["parents"] = [parent]

        file = self.files.copy(
            fileId=document_id, body=body, fields="id", supportsAllDrives=True
        ).execute()

        return file.get("id")

    def move_document(self, document_id, parent):
        """
        Moves a document in owner's Google Drive to the specified folder.

        :param: document_id ID of document to be moved
        :param: parent Destination folder

        :returns: Moved document's ID
        """

        prev = ",".join(self.get_parents(document_id))

        file = self.files.update(
            fileId=document_id,
            addParents=parent,
            removeParents=prev,
            fields="id, parents",
            supportsAllDrives=True,
        ).execute()

        return file.get("id")

    def update_document(self, document_id, mappings):
        """
        Updates an output document in owner's Google Drive with provided mappings.

        :returns: docs.batchUpdate results
        """

        if len(mappings) == 0:
            return None

        requests = []
        for (src, dest) in mappings.items():
            requests.append(
                {
                    "replaceAllText": {
                        "containsText": {
                            "text": src,
                            "matchCase": "true",
                        },
                        "replaceText": dest,
                    }
                }
            )

        body = {"requests": requests}
        results = self.docs.batchUpdate(documentId=document_id, body=body).execute()

        return results

    def get_parents(self, document_id):
        """
        Return parents of the given document.
        """

        file = self.files.get(
            fileId=document_id, fields="parents", supportsAllDrives=True
        ).execute()

        return file.get("parents")

    def add_user(self, document_id, email, role="reader"):
        body = {"type": "user", "role": role, "emailAddress": email}
        permissions = self.permissions.create(
            fileId=document_id, body=body, supportsAllDrives=True
        ).execute()

        return permissions
