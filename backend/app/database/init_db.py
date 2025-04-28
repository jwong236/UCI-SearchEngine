import sqlite3
import os

# Create database directory if it doesn't exist
os.makedirs("backend/app/database", exist_ok=True)

# Connect to SQLite database (creates it if it doesn't exist)
conn = sqlite3.connect("backend/app/database/crawler.db")
cursor = conn.cursor()

# Create tables
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT UNIQUE NOT NULL,
    domain TEXT NOT NULL,
    status_code INTEGER,
    last_crawled TIMESTAMP,
    is_completed BOOLEAN DEFAULT FALSE,
    title TEXT,
    content TEXT
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS url_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_url_id INTEGER,
    target_url_id INTEGER,
    FOREIGN KEY (source_url_id) REFERENCES urls (id),
    FOREIGN KEY (target_url_id) REFERENCES urls (id)
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS domain_rate_limits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT UNIQUE NOT NULL,
    last_request TIMESTAMP,
    delay_seconds FLOAT DEFAULT 1.0
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS crawl_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    urls_crawled INTEGER DEFAULT 0,
    urls_failed INTEGER DEFAULT 0,
    unique_domains INTEGER DEFAULT 0
)
"""
)

# Commit changes and close connection
conn.commit()
conn.close()

print("Database initialized successfully!")
