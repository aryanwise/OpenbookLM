import sqlite3
import os
import hashlib

class DBManager:
    def __init__(self, project_path):
        self.db_path = os.path.join(project_path, "project_data.db")
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Table 1: Track indexed files to prevent re-embedding
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS file_registry (
                filename TEXT PRIMARY KEY,
                file_hash TEXT,
                indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table 2: Chat History (Better than JSON for appending)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT,
                content TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def get_file_hash(self, filename):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT file_hash FROM file_registry WHERE filename = ?", (filename,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def update_file_hash(self, filename, file_hash):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO file_registry (filename, file_hash)
            VALUES (?, ?)
        ''', (filename, file_hash))
        conn.commit()
        conn.close()

    def add_chat_message(self, role, content):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chat_history (role, content) VALUES (?, ?)", (role, content))
        conn.commit()
        conn.close()

    def get_chat_history(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT role, content FROM chat_history ORDER BY id ASC")
        history = [{"role": row[0], "content": row[1]} for row in cursor.fetchall()]
        conn.close()
        return history

    @staticmethod
    def calculate_file_hash(file_path):
        """Helper to get MD5 hash of a file"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()