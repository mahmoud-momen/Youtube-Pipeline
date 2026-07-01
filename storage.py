"""
storage.py
Creates the SQLite database and loads transformed data into it.
"""

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path("data/youtube_pipeline.db")


class Storage:

    def __init__(self):
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self._create_tables()

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS videos (
                video_id      TEXT PRIMARY KEY,
                title         TEXT,
                channel_name  TEXT,
                channel_id    TEXT,
                published_at  TEXT,
                description   TEXT,
                view_count    INTEGER DEFAULT 0,
                like_count    INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS comments (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                video_id      TEXT,
                author        TEXT,
                text          TEXT,
                published_at  TEXT,
                FOREIGN KEY (video_id) REFERENCES videos(video_id)
            );
        """)
        self.conn.commit()
        logger.info("Tables ready.")

    def load_videos(self, videos: list):
        self.conn.executemany("""
            INSERT OR IGNORE INTO videos
            (video_id, title, channel_name, channel_id, published_at, description, view_count, like_count, comment_count)
            VALUES (:video_id, :title, :channel_name, :channel_id, :published_at, :description, :view_count, :like_count, :comment_count)
        """, videos)
        self.conn.commit()
        logger.info("Loaded %s videos into database.", len(videos))

    def load_comments(self, comments: list):
        self.conn.executemany("""
            INSERT INTO comments (video_id, author, text, published_at)
            VALUES (:video_id, :author, :text, :published_at)
        """, comments)
        self.conn.commit()
        logger.info("Loaded %s comments into database.", len(comments))

    def close(self):
        self.conn.close()