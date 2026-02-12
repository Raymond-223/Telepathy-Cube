from __future__ import annotations

import sqlite3
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sentient_cube.models import ObjectMemory


class SpatialMemoryDB:
    def __init__(self, db_path: str = "spatial_memory.db") -> None:
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                location TEXT NOT NULL,
                confidence REAL NOT NULL,
                timestamp TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def add_object(self, memory: ObjectMemory) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO objects (name, location, confidence, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (memory.name, memory.location, memory.confidence, memory.timestamp.isoformat()),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def latest_object(self, name: str) -> Optional[ObjectMemory]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT name, location, confidence, timestamp
            FROM objects
            WHERE name = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            (name,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return ObjectMemory(
            name=row["name"],
            location=row["location"],
            confidence=float(row["confidence"]),
            timestamp=datetime.fromisoformat(row["timestamp"]),
        )

    def history(self, name: str, limit: int = 10) -> List[ObjectMemory]:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT name, location, confidence, timestamp
            FROM objects
            WHERE name = ?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (name, limit),
        )
        rows = cur.fetchall()
        return [
            ObjectMemory(
                name=row["name"],
                location=row["location"],
                confidence=float(row["confidence"]),
                timestamp=datetime.fromisoformat(row["timestamp"]),
            )
            for row in rows
        ]

    def close(self) -> None:
        self.conn.close()

    @staticmethod
    def as_dict(memory: ObjectMemory) -> dict:
        payload = asdict(memory)
        payload["timestamp"] = memory.timestamp.isoformat()
        return payload

