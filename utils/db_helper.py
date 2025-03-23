import sqlite3
from datetime import datetime
import traceback

class DatabaseHelper:
    def __init__(self, db_name='notes.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.initialize_db()  # Changed to private method
        self.schema_updated = False  # Add a flag to track schema updates
        self.update_schema() 
                
    def initialize_db(self):  # Private initialization method
        """Initialize database and schema"""
        try:
            cursor = self.connect()
            
            # Create notes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_pinned INTEGER DEFAULT 0,
                    is_locked INTEGER DEFAULT 0,
                    folder_id INTEGER DEFAULT NULL,
                    tags TEXT DEFAULT NULL
                )
            ''')
            
            # Create folders table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS folders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    is_locked INTEGER DEFAULT 0,
                    password TEXT DEFAULT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create default folder if it doesn't exist
            cursor.execute('SELECT id FROM folders WHERE id = 1')
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO folders (id, name, is_locked)
                    VALUES (1, 'Default', 0)
                ''')
            
            self.conn.commit()
        finally:
            self.close()

    def connect(self):
        """Establish a connection to the database."""
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row  # This enables column access by name
        self.cursor = self.conn.cursor()
        return self.cursor

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None

    def get_all_notes(self, folder_id=None):
        """
        Retrieve notes from the database.
        If folder_id is None, return only notes not in any folder.
        If folder_id is specified, return notes from that folder.
        """
        try:
            cursor = self.connect()
            if folder_id is None:
                # Only return notes not assigned to any folder
                cursor.execute("SELECT * FROM notes WHERE folder_id IS NULL ORDER BY is_pinned DESC, updated_at DESC")
            else:
                # Return notes from specific folder
                cursor.execute("SELECT * FROM notes WHERE folder_id = ? ORDER BY is_pinned DESC, updated_at DESC", (folder_id,))
            return cursor.fetchall()
        finally:
            self.close()

    def is_folder_locked(self, folder_id, folder_name):
        """Check if a folder is locked."""
        try:
            cursor = self.connect()
            cursor.execute("SELECT is_locked FROM folders WHERE id = ?", (folder_id,))
            result = cursor.fetchone()
            return result and result['is_locked'] == 1
        finally:
            self.close()
            
            # Check if folder is locked
            folder_info = self.db.get_folder(folder_id)  # Make sure this method exists in your DB helper
            if folder_info and folder_info['is_locked']:
                # Show password dialog
                self.show_folder_password_dialog(folder_id, folder_name)
            else:
                # Open the folder directly
                self.open_folder(folder_id, folder_name)
                
    def get_folder(self, folder_id):
        """Get folder information by ID"""
        try:
            cursor = self.connect()
            cursor.execute(
                "SELECT id, name, is_locked FROM folders WHERE id = ?", 
                (folder_id,)
            )
            result = cursor.fetchone()
            if result:
                return {
                    'id': result['id'],
                    'name': result['name'],
                    'is_locked': result['is_locked']
                }
            return None
        except Exception as e:
            print(f"Error getting folder: {e}")
            return None
        finally:
            self.close()

    def check_folder_password(self, folder_id, password):
        """Check if the provided password matches the folder's password."""
        print(f"Checking password for folder {folder_id}...")  # Debug print
        try:
            cursor = self.connect()
            cursor.execute("SELECT password FROM folders WHERE id = ?", (folder_id,))
            result = cursor.fetchone()
            if result and result['password'] == password:
                print("Password match!")  # Debug print
                return True
            print("Password mismatch or folder not found.")  # Debug print
            return False
        finally:
            self.close()

    def get_note_by_id(self, note_id):
        """Retrieve a specific note by ID."""
        try:
            cursor = self.connect()
            cursor.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
            return cursor.fetchone()
        finally:
            self.close()

    def add_note(self, title, content):
        """Add a new note to the database."""
        try:
            cursor = self.connect()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                "INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (title, content, current_time, current_time)
            )
            self.conn.commit()
            return cursor.lastrowid  # Return the ID of the newly created note
        finally:
            self.close()
                        

    def update_note(self, note_id, title, content):
                
        """Update an existing note."""
        try:
            cursor = self.connect()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                "UPDATE notes SET title = ?, content = ?, updated_at = ? WHERE id = ?",
                (title, content, current_time, note_id)
            )
            self.conn.commit()
            return cursor.rowcount > 0  # Return True if the update was successful
        finally:
            self.close()

    def delete_note(self, note_id):
        """Delete a note from the database."""
        try:
            cursor = self.connect()
            cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            self.conn.commit()
            return cursor.rowcount > 0  # Return True if the deletion was successful
        finally:
            self.close()

    def search_notes(self, query):
        """Search for notes by title or content."""
        try:
            cursor = self.connect()
            cursor.execute(
                "SELECT * FROM notes WHERE title LIKE ? OR content LIKE ? ORDER BY updated_at DESC",
                (f'%{query}%', f'%{query}%')
            )
            return cursor.fetchall()
        finally:
            self.close()
            
    # Add methods for pinning/unpinning notes
    def pin_note(self, note_id):
        """Pin a note to the top."""
        try:
            cursor = self.connect()
            cursor.execute("UPDATE notes SET is_pinned = 1 WHERE id = ?", (note_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        finally:
            self.close()

    def unpin_note(self, note_id):
        """Unpin a note."""
        try:
            cursor = self.connect()
            cursor.execute("UPDATE notes SET is_pinned = 0 WHERE id = ?", (note_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        finally:
            self.close()

    # Add methods for locked folders
    def create_folder(self, name, is_locked=0, password=None):
        """Create a new folder."""
        try:
            cursor = self.connect()
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(
                "INSERT INTO folders (name, is_locked, password, created_at) VALUES (?, ?, ?, ?)",
                (name, is_locked, password, current_time)
            )
            self.conn.commit()
            return cursor.lastrowid
        finally:
            self.close()

    def get_all_folders(self):
        """Get all folders with note counts."""
        try:
            cursor = self.connect()
            cursor.execute("""
                SELECT 
                    f.id, 
                    f.name, 
                    f.is_locked, 
                    f.password,
                    f.created_at,
                    COUNT(n.id) as note_count 
                FROM folders f 
                LEFT JOIN notes n ON f.id = n.folder_id 
                GROUP BY f.id, f.name, f.is_locked, f.password, f.created_at
                ORDER BY f.name
            """)
            folders = cursor.fetchall()
            return [dict(folder) for folder in folders]
        except Exception as e:
            print(f"Error getting folders: {e}")
            return []
        finally:
            self.close()

    def move_note_to_folder(self, note_id, folder_id):
        """Move a note to a folder."""
        try:
            cursor = self.connect()
            cursor.execute("UPDATE notes SET folder_id = ? WHERE id = ?", (folder_id, note_id))
            self.conn.commit()
            return cursor.rowcount > 0
        finally:
            self.close()

    def get_notes_by_folder(self, folder_id):
        """Get all notes in a folder, with proper ordering."""
        try:
            cursor = self.connect()
            if folder_id is None:
                # Get notes not in any folder
                cursor.execute("""
                    SELECT * FROM notes 
                    WHERE folder_id IS NULL 
                    ORDER BY is_pinned DESC, updated_at DESC
                """)
            else:
                # Get notes from specific folder
                cursor.execute("""
                    SELECT * FROM notes 
                    WHERE folder_id = ? 
                    ORDER BY is_pinned DESC, updated_at DESC
                """, (folder_id,))
            return cursor.fetchall()
        finally:
            self.close()

    def check_folder_password(self, folder_id, password):
        """Check if the provided password matches the folder's password."""
        try:
            cursor = self.connect()
            cursor.execute("SELECT password FROM folders WHERE id = ?", (folder_id,))
            result = cursor.fetchone()
            if result and result['password'] == password:
                return True
            return False
        finally:
            self.close()

    def update_note_tags(self, note_id, tags):
        """Update the tags for a note."""
        try:
            cursor = self.connect()
            cursor.execute("UPDATE notes SET tags = ? WHERE id = ?", (tags, note_id))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating note tags: {e}")
            return False
        finally:
            self.close()
            
    def can_access_folder(self, folder_id, provided_password=None):
        """Check if a folder can be accessed with the given password."""
        try:
            cursor = self.connect()
            cursor.execute("SELECT is_locked, password FROM folders WHERE id = ?", (folder_id,))
            folder = cursor.fetchone()
            
            if not folder:
                return False  # Folder doesn't exist
                
            if folder['is_locked'] == 0:
                return True  # Not locked, can access
                
            # Folder is locked, check password
            if provided_password and folder['password'] == provided_password:
                return True
                
            return False  # Locked and no/wrong password
        finally:
            self.close()
            
    def delete_folder(self, folder_id):
        """Delete a folder and optionally its notes."""
        try:
            cursor = self.connect()
            # First move all notes in this folder back to "no folder" (NULL)
            cursor.execute("UPDATE notes SET folder_id = NULL WHERE folder_id = ?", (folder_id,))
            # Then delete the folder
            cursor.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        finally:
            self.close()
        
    def update_schema(self):
        if self.schema_updated:
            return  # Exit if the schema has already been updated
        print("Updating database schema...")  # Debug print
        print(f"Called from: {traceback.format_stack()}")  # Print the call stack
        """Update the database schema if needed"""
        try:
            cursor = self.connect()
            # Check the existing columns in the notes table
            cursor.execute("PRAGMA table_info(notes)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Add missing columns
            if 'is_pinned' not in columns:
                cursor.execute("ALTER TABLE notes ADD COLUMN is_pinned INTEGER DEFAULT 0")
            if 'folder_id' not in columns:
                cursor.execute("ALTER TABLE notes ADD COLUMN folder_id INTEGER DEFAULT NULL")
            if 'is_locked' not in columns:
                cursor.execute("ALTER TABLE notes ADD COLUMN is_locked INTEGER DEFAULT 0")
            if 'tags' not in columns:
                cursor.execute("ALTER TABLE notes ADD COLUMN tags TEXT DEFAULT NULL")
            
            self.conn.commit()
            self.conn.commit()
            self.schema_updated = True  # Set the flag to True after updating
        finally:
            self.close()