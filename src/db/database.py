#!/usr/bin/env python3
"""
Database utilities for AllSeeingEye.
"""

import sqlite3
from typing import List, Dict, Any

class Database:
    """Handles database operations."""

    def __init__(self, db_path="allseeingeye.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        """Creates the database tables."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY,
                    path TEXT UNIQUE,
                    category TEXT,
                    size INTEGER,
                    last_modified TEXT
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY,
                    file_id INTEGER,
                    content TEXT,
                    FOREIGN KEY (file_id) REFERENCES files (id)
                )
            """)
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    id INTEGER PRIMARY KEY,
                    chunk_id INTEGER,
                    embedding BLOB,
                    FOREIGN KEY (chunk_id) REFERENCES chunks (id)
                )
            """)

    def insert_file(self, path: str, category: str, size: int, last_modified: str) -> int:
        """Inserts a file into the database."""
        with self.conn:
            cursor = self.conn.execute(
                "INSERT OR IGNORE INTO files (path, category, size, last_modified) VALUES (?, ?, ?, ?)",
                (path, category, size, last_modified)
            )
            if cursor.lastrowid:
                return cursor.lastrowid
            else:
                return self.conn.execute("SELECT id FROM files WHERE path = ?", (path,)).fetchone()[0]

    def insert_chunk(self, file_id: int, content: str) -> int:
        """Inserts a chunk into the database."""
        with self.conn:
            cursor = self.conn.execute(
                "INSERT INTO chunks (file_id, content) VALUES (?, ?)",
                (file_id, content)
            )
            return cursor.lastrowid

    def insert_embedding(self, chunk_id: int, embedding: List[float]):
        """Inserts an embedding into the database."""
        import numpy as np
        with self.conn:
            self.conn.execute(
                "INSERT INTO embeddings (chunk_id, embedding) VALUES (?, ?)",
                (chunk_id, np.array(embedding, dtype=np.float32).tobytes())
            )

    def get_all_chunks(self) -> List[Dict[str, Any]]:
        """Gets all chunks from the database."""
        with self.conn:
            cursor = self.conn.execute("SELECT id, content FROM chunks")
            return [{"id": row[0], "content": row[1]} for row in cursor.fetchall()]
