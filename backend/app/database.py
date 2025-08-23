"""Simple SQLite-based database utilities for AI Tutoring MVP.

Uses Python's built-in sqlite3 module to persist user data. This avoids external
dependencies like SQLAlchemy, which may not be installed in the execution
environment. The database is initialized automatically when imported.
"""

import sqlite3
import os

# Path to the SQLite database file
DB_FILENAME = "ai_tutoring.db"
DB_PATH = os.path.join(os.path.dirname(__file__), DB_FILENAME)


def init_db() -> None:
    """Initialize the SQLite database by creating necessary tables if they do not exist.

    This function also ensures that any new columns added in future versions (e.g., xp, level,
    streak_count, last_streak_date) exist on the users table. SQLite does not support
    IF NOT EXISTS syntax for individual columns, so we query the table info and alter
    the schema if required. Running this function multiple times is safe.
    """
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        # Create the users table with basic columns; additional columns are added below if missing
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                hashed_password TEXT NOT NULL,
                role TEXT NOT NULL
            )
            """
        )
        # Create table for chat messages to track progress/history. A thread_id
        # column is added later if missing to support multiple conversation threads.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        # Create table for conversation threads. Each thread belongs to a user
        # and groups messages into separate study sessions or topics. The name
        # allows the user to label threads (e.g., "Algebra Practice").
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS threads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        # Summaries table stores condensed representations of long conversation
        # threads.  Each entry is uniquely identified by the owning user and
        # thread.  The summary text may be regenerated over time as more
        # messages are added.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS summaries (
                user_id INTEGER NOT NULL,
                thread_id INTEGER NOT NULL,
                summary TEXT,
                PRIMARY KEY (user_id, thread_id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (thread_id) REFERENCES threads(id)
            )
            """
        )
        # Create table for subscriptions
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'inactive',
                start_date DATETIME,
                end_date DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        # Create table for topics. Each topic represents a subject or area of study
        # available in the tutoring system. Names are unique to prevent duplicates.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT
            )
            """
        )

        # Create table for study goals. Goals allow a user to set a target number
        # of sessions for a given topic with optional description and due date.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topic_id INTEGER NOT NULL,
                description TEXT,
                target_sessions INTEGER NOT NULL,
                completed_sessions INTEGER NOT NULL DEFAULT 0,
                created_at TEXT DEFAULT (DATETIME('now')),
                due_date TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (topic_id) REFERENCES topics(id)
            )
            """
        )

        # Create table for user feedback on study materials. Each entry records
        # which user rated which topic, the numeric rating and optional
        # comments.  Feedback helps improve content quality over time.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                topic_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                comments TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (topic_id) REFERENCES topics(id)
            )
            """
        )

        # Create table for study plans. A plan groups multiple goals for a user
        # and includes scheduling information such as due dates and recurring
        # cadence (e.g. weekly).
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                due_date TEXT,
                recurrence TEXT,
                created_at TEXT DEFAULT (DATETIME('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        # Linking table between plans and goals. Each plan can reference
        # multiple goals and a goal can belong to multiple plans if desired.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS plan_goals (
                plan_id INTEGER NOT NULL,
                goal_id INTEGER NOT NULL,
                FOREIGN KEY (plan_id) REFERENCES plans(id),
                FOREIGN KEY (goal_id) REFERENCES goals(id)
            )
            """
        )
        # Ensure progress-related columns exist in users table
        # xp: cumulative experience points
        # level: integer level derived from xp
        # streak_count: number of consecutive days of activity
        # last_streak_date: ISO date string for last activity used to compute streak
        cursor.execute("PRAGMA table_info(users)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        # Each entry is a tuple: (cid, name, type, notnull, dflt_value, pk)
        progress_columns = {
            "xp": "INTEGER DEFAULT 0",
            "level": "INTEGER DEFAULT 0",
            "streak_count": "INTEGER DEFAULT 0",
            "last_streak_date": "TEXT"
        }
        for col_name, col_def in progress_columns.items():
            if col_name not in existing_cols:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
        conn.commit()

        # Ensure the thread_id column exists in the messages table. This column
        # associates each message with a specific thread. It is added here if
        # missing from a previous version of the database. Existing messages
        # will be updated to belong to a default thread later in application
        # logic.
        cursor.execute("PRAGMA table_info(messages)")
        msg_cols = {row[1] for row in cursor.fetchall()}
        if "thread_id" not in msg_cols:
            cursor.execute("ALTER TABLE messages ADD COLUMN thread_id INTEGER")
            conn.commit()

        # Pre-populate the topics table with commonly requested subjects if it is empty.
        # These topics are drawn from widely used tutoring curricula, including core math,
        # science, language arts, languages, programming and history/social studies.
        # This eliminates decision fatigue for new users and provides a sensible
        # starting point. Refer to educational subject listings for inspiration【256241168915814†L29-L144】.
        cursor.execute("SELECT COUNT(*) FROM topics")
        count = cursor.fetchone()[0]
        if count == 0:
            default_topics = [
                ("Elementary Math", "Fundamental arithmetic and number sense"),
                ("Algebra I", "Introductory algebraic concepts and linear equations"),
                ("Algebra II", "Quadratic equations, polynomials and advanced algebra"),
                ("Geometry", "Shapes, proofs and basic trigonometry"),
                ("Pre-Calculus", "Functions, sequences and trigonometric identities"),
                ("Calculus", "Differential and integral calculus concepts"),
                ("Statistics", "Descriptive and inferential statistics"),
                ("Biology", "Cell structure, genetics and ecosystems"),
                ("Chemistry", "Atomic theory, reactions and stoichiometry"),
                ("Physics", "Motion, forces and energy principles"),
                ("Reading & Literature", "Reading comprehension and literary analysis"),
                ("Grammar & Writing", "Grammar, punctuation and essay writing"),
                ("Spanish Language", "Introductory Spanish vocabulary and grammar"),
                ("French Language", "Introductory French vocabulary and grammar"),
                ("Python Programming", "Fundamentals of Python programming"),
                ("Java Programming", "Object-oriented Java programming basics"),
                ("U.S. History", "Major events and themes in United States history"),
                ("World History", "Global historical events and civilizations"),
                ("Study Skills & Time Management", "Effective study strategies and time management"),
                ("SAT/ACT Prep", "Strategies and practice for standardized tests")
            ]
            cursor.executemany(
                "INSERT INTO topics (name, description) VALUES (?, ?)", default_topics
            )
            conn.commit()
    finally:
        conn.close()


def get_db():
    """FastAPI dependency that yields a thread-safe SQLite connection.

    SQLite connections are, by default, bound to the thread that created them.
    FastAPI may serve requests in multiple threads, so using a connection from
    another thread raises a ProgrammingError. To avoid this, we set
    `check_same_thread=False` on the connection, which relaxes the threading
    restriction. Each request still receives its own dedicated connection, which
    is closed after the request completes.
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


# Initialize the database when this module is imported
init_db()