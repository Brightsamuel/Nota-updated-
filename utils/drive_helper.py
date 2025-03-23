import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from kivy.app import App
from kivy.utils import platform
from kivy.storage.jsonstore import JsonStore
from threading import Thread

class DriveHelper:
    def __init__(self, credentials_path='client_secrets.json', settings_path='settings.yaml'):
        self.credentials_path = credentials_path
        self.settings_path = settings_path
        self.is_authenticated = False
        self.drive = None
        
        # Create data directory if needed
        self.data_dir = os.path.join(os.path.expanduser('~'), '.notesapp')
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        # Full paths for credentials and settings
        self.credentials_file = os.path.join(self.data_dir, credentials_path)
        self.settings_file = os.path.join(self.data_dir, settings_path)
        
        # Store for keeping track of uploaded notes
        self.store = JsonStore(os.path.join(self.data_dir, 'drive_uploads.json'))

    def authenticate(self, callback=None):
        """Authenticate with Google Drive API"""
        try:
            print("Starting Google Drive authentication...")  # Debugging log
            
            # Check if PyDrive is installed
            try:
                from pydrive.auth import GoogleAuth
            except ImportError:
                print("PyDrive not installed.")  # Debugging log
                return False, "PyDrive not installed. Please install pydrive2 package."
            
            # Run authentication in a separate thread to avoid blocking UI
            def auth_thread():
                try:
                    # Create settings file if it doesn't exist
                    if not os.path.exists(self.settings_file):
                        self._create_default_settings()
                    
                    gauth = GoogleAuth(settings_file=self.settings_file)

                    # Try to load saved client credentials
                    gauth.LoadCredentialsFile(os.path.join(self.data_dir, "credentials.json"))
                    print("Loaded credentials file.")  # Debugging log
                    
                    if gauth.credentials is None:
                        print("No existing credentials, starting authentication...")  # Debugging log
                        gauth.CommandLineAuth()  # This might be causing the hang
                    elif gauth.access_token_expired:
                        print("Refreshing expired credentials...")  # Debugging log
                        gauth.Refresh()
                    else:
                        print("Using existing credentials...")  # Debugging log
                        gauth.Authorize()
                    
                    # Save the credentials for future use
                    gauth.SaveCredentialsFile(os.path.join(self.data_dir, "credentials.json"))
                    print("Credentials saved.")  # Debugging log
                    
                    # Create Drive instance
                    self.drive = GoogleDrive(gauth)
                    self.is_authenticated = True

                    print("Google Drive authentication successful.")  # Debugging log
                    if callback:
                        callback(True, "Authentication successful")
                    return True, "Authentication successful"
                except Exception as e:
                    print(f"Authentication failed: {str(e)}")  # Debugging log
                    if callback:
                        callback(False, f"Authentication failed: {str(e)}")
                    return False, f"Authentication failed: {str(e)}"

            thread = Thread(target=auth_thread)
            thread.daemon = True
            thread.start()
            
            return True, "Authentication started"
        except Exception as e:
            print(f"Authentication error: {str(e)}")  # Debugging log
            return False, f"Authentication error: {str(e)}"


    def _create_default_settings(self):
        """Create default settings.yaml file for PyDrive"""
        settings = """client_config_backend: file
            client_config_file: {0}
            save_credentials: True
            save_credentials_backend: file
            save_credentials_file: {1}
            get_refresh_token: True
            oauth_scope:
        - https://www.googleapis.com/auth/drive.file
        - https://www.googleapis.com/auth/drive.metadata.readonly""".format(
            self.credentials_file, os.path.join(self.data_dir, "credentials.json")
        )
        
        with open(self.settings_file, 'w') as f:
            f.write(settings)

    def upload_note(self, note_id, title, content, callback=None):
        """Upload a note to Google Drive and return the file URL."""
        if not self.is_authenticated or not self.drive:
            success, message = self.authenticate()
            if not success:
                if callback:
                    callback(False, message)
                return False, message

        try:
            # Create a new file in Google Drive
            file = self.drive.CreateFile({'title': title, 'mimeType': 'text/plain'})
            file.SetContentString(content)
            file.Upload()

            # Get the uploaded file's ID
            file_id = file['id']

            # Make the file publicly accessible (optional)
            file.InsertPermission({
                'type': 'anyone',
                'value': 'anyone',
                'role': 'reader'
            })

            # Generate the public URL
            file_url = f"https://drive.google.com/file/d/{file_id}/view"

            # Store file ID mapping
            self.store.put(str(note_id), drive_id=file_id, title=title)

            message = f"Note '{title}' uploaded. URL: {file_url}"

            if callback:
                callback(True, message)

            return True, file_url  # Return the success status and file URL

        except Exception as e:
            message = f"Upload failed: {str(e)}"
            if callback:
                callback(False, message)
            return False, message

    def update_note(self, note_id, title, content, callback=None):
        """Update an existing note on Google Drive"""
        if not self.is_authenticated or not self.drive:
            success, message = self.authenticate()
            if not success:
                if callback:
                    callback(False, message)
                return False, message
        
        try:
            # Check if note exists in our store
            if not self.store.exists(str(note_id)):
                return self.upload_note(note_id, title, content, callback)
            
            # Get file ID from store
            note_data = self.store.get(str(note_id))
            file_id = note_data['drive_id']
            
            # Get the file from Drive
            file = self.drive.CreateFile({'id': file_id})
            file['title'] = title  # Update title if changed
            file.SetContentString(content)
            file.Upload()  # Update content
            
            message = f"Note '{title}' updated on Google Drive"
            if callback:
                callback(True, message)
            return True, message
        
        except Exception as e:
            message = f"Update failed: {str(e)}"
            if callback:
                callback(False, message)
            return False, message

    def get_uploaded_notes(self):
        """Get list of notes that have been uploaded to Drive"""
        uploaded_notes = []
        for key in self.store.keys():
            uploaded_notes.append({
                'note_id': int(key),
                'drive_id': self.store.get(key)['drive_id'],
                'title': self.store.get(key)['title']
            })
        return uploaded_notes