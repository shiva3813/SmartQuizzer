import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_DIR = Path("data")
DB_PATH = DB_DIR / "smartquizzer.db"


def _connect():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                questions_json TEXT NOT NULL,
                source_name TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                score INTEGER NOT NULL,
                total INTEGER NOT NULL,
                percentage REAL NOT NULL,
                submitted_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def save_questions(questions, source_name="Uploaded PDF"):
    created_at = datetime.utcnow().isoformat()
    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO quizzes (questions_json, source_name, created_at)
            VALUES (?, ?, ?)
            """,
            (json.dumps(questions), source_name, created_at),
        )
        connection.commit()
        return cursor.lastrowid


def load_questions():
    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT questions_json FROM quizzes
            ORDER BY id DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        if not row:
            return []
        return json.loads(row["questions_json"])


def save_attempt(score, total, user_name="Guest"):
    percentage = (score / total * 100) if total else 0.0
    submitted_at = datetime.utcnow().isoformat()
    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO attempts (user_name, score, total, percentage, submitted_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_name, score, total, percentage, submitted_at),
        )
        connection.commit()
        return cursor.lastrowid


def load_attempts(limit=20):
    with _connect() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT user_name, score, total, percentage, submitted_at
            FROM attempts
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()

    scores = [row["score"] for row in rows]
    return {
        "tests_taken": len(rows),
        "scores": list(reversed(scores)),
        "recent": [dict(row) for row in rows],
    }
