import sqlite3
import os

DB_DIR = "database"
DB_PATH = os.path.join(DB_DIR, "notes.db")

# Ensure the database directory exists
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# Initialize the database and create the notes table
def init_db():
    try:
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        connection.commit()
        connection.close()
        print("Database initialized successfully.")
    except sqlite3.OperationalError as e:
        print("Error while connecting to the database:", e)

# Add a new note entry to the database
def add_note(title, content):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("INSERT INTO notes (title, content) VALUES (?, ?)", (title, content))
    connection.commit()
    connection.close()

# Update an existing note
def update_note(note_id, title, content):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("UPDATE notes SET title = ?, content = ?, timestamp = CURRENT_TIMESTAMP WHERE id = ?", 
                   (title, content, note_id))
    connection.commit()
    connection.close()

# Delete a note
def delete_note(note_id):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    connection.commit()
    connection.close()

# Fetch all notes
def fetch_notes():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("SELECT id, title, content, timestamp FROM notes")
    notes = cursor.fetchall()
    connection.close()
    return notes
