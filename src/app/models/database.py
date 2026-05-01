# database.py - Database connection and schema management

import os
import sqlite3
from typing import Optional


class Database:
    """Database connection and management class."""
    
    @staticmethod
    def get_db():
        """Get database connection with row factory."""
        conn = sqlite3.connect(Database._db_path())
        conn.row_factory = sqlite3.Row
        return conn
    
    @staticmethod
    def _db_path() -> str:
        """SQLite path; override with PERFORMANCELENS_DB_PATH for Tauri/Electron bundles."""
        return os.environ.get(
            'PERFORMANCELENS_DB_PATH',
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'performance.db'),
        )
    
    @staticmethod
    def init_db():
        """Initialize database with all required tables."""
        conn = Database.get_db()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT NOT NULL,
                pin_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS subjects (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            );
            CREATE TABLE IF NOT EXISTS results (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                term_name   TEXT NOT NULL,
                school_year TEXT NOT NULL DEFAULT '',
                term_label  TEXT NOT NULL DEFAULT '',
                subject     TEXT NOT NULL,
                score       REAL NOT NULL,
                user_id INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS marking_scheme (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                grade_label TEXT NOT NULL,
                min_score   REAL NOT NULL,
                max_score   REAL NOT NULL,
                sort_order  INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS study_availability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                day_of_week INTEGER NOT NULL,
                start_minutes INTEGER NOT NULL,
                end_minutes INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS study_preferences (
                user_id INTEGER PRIMARY KEY DEFAULT 1,
                weak_subject_multiplier REAL NOT NULL DEFAULT 1.75,
                session_length_min INTEGER NOT NULL DEFAULT 45,
                break_min INTEGER NOT NULL DEFAULT 10,
                max_blocks_per_day INTEGER NOT NULL DEFAULT 8,
                weekend_intensity REAL NOT NULL DEFAULT 1.0,
                reserve_weekly_minutes INTEGER NOT NULL DEFAULT 90,
                min_session_min INTEGER NOT NULL DEFAULT 20,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS study_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                title TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                plan_json TEXT NOT NULL
            );
        """)

        # Seed default scheme only if table is empty
        existing = conn.execute('SELECT COUNT(*) FROM marking_scheme').fetchone()[0]
        if existing == 0:
            conn.executemany(
                'INSERT INTO marking_scheme (grade_label, min_score, max_score, sort_order) VALUES (?, ?, ?, ?)',
                [
                    ('A',  76, 100, 1),
                    ('B',  66,  75, 2),
                    ('C+', 56,  65, 3),
                    ('C-', 46,  55, 4),
                    ('D',  40,  45, 5),
                    ('F',   0,  39, 6),
                ]
            )
        
        conn.commit()
        Database._migrate_results_schema(conn)
        Database._migrate_study_schema(conn)
        conn.close()

    @staticmethod
    def _migrate_results_schema(conn: sqlite3.Connection):
        """Add school_year / term_label / user_id to existing DBs; backfill term_label from term_name."""
        cols = {row[1] for row in conn.execute('PRAGMA table_info(results)').fetchall()}
        if 'school_year' not in cols:
            conn.execute("ALTER TABLE results ADD COLUMN school_year TEXT NOT NULL DEFAULT ''")
        if 'term_label' not in cols:
            conn.execute("ALTER TABLE results ADD COLUMN term_label TEXT NOT NULL DEFAULT ''")
        if 'user_id' not in cols:
            conn.execute("ALTER TABLE results ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1")
        conn.commit()
        conn.execute("""
            UPDATE results
            SET term_label = TRIM(term_name)
            WHERE TRIM(COALESCE(term_label, '')) = ''
              AND TRIM(COALESCE(term_name, '')) != ''
        """)
        conn.commit()

    @staticmethod
    def _migrate_study_schema(conn: sqlite3.Connection):
        """Create and populate study-related tables."""
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS study_availability (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                day_of_week INTEGER NOT NULL,
                start_minutes INTEGER NOT NULL,
                end_minutes INTEGER NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS study_preferences (
                user_id INTEGER PRIMARY KEY DEFAULT 1,
                weak_subject_multiplier REAL NOT NULL DEFAULT 1.75,
                session_length_min INTEGER NOT NULL DEFAULT 45,
                break_min INTEGER NOT NULL DEFAULT 10,
                max_blocks_per_day INTEGER NOT NULL DEFAULT 8,
                weekend_intensity REAL NOT NULL DEFAULT 1.0,
                reserve_weekly_minutes INTEGER NOT NULL DEFAULT 90,
                min_session_min INTEGER NOT NULL DEFAULT 20,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS study_schedules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL DEFAULT 1,
                title TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                plan_json TEXT NOT NULL
            )
            """
        )
        conn.commit()
        
        n = conn.execute('SELECT COUNT(*) FROM study_preferences').fetchone()[0]
        if n == 0:
            from datetime import datetime, timezone
            conn.execute(
                """
                INSERT INTO study_preferences (user_id, updated_at) VALUES (1, ?)
                """,
                (datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),),
            )
            conn.commit()
