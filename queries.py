"""
queries.py
Runs 3 analytical queries against the SQLite database and prints results.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/youtube_pipeline.db")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row


def run_query(title: str, sql: str):
    print(f"\n{'='*60}")
    print(f"Query: {title}")
    print('='*60)
    rows = conn.execute(sql).fetchall()
    for row in rows:
        print(dict(row))
    return rows


# Query 1: Top 5 videos by view count
run_query(
    "Top 5 Videos by View Count",
    """
    SELECT title, channel_name, view_count, like_count, comment_count
    FROM videos
    ORDER BY view_count DESC
    LIMIT 5;
    """
)

# Query 2: Average views, likes, and comments per channel
run_query(
    "Average Engagement per Channel",
    """
    SELECT
        channel_name,
        COUNT(*)                        AS total_videos,
        ROUND(AVG(view_count), 0)       AS avg_views,
        ROUND(AVG(like_count), 0)       AS avg_likes,
        ROUND(AVG(comment_count), 0)    AS avg_comments
    FROM videos
    GROUP BY channel_name
    ORDER BY avg_views DESC;
    """
)

# Query 3: Most active commenters across all videos
run_query(
    "Top 10 Most Active Commenters",
    """
    SELECT author, COUNT(*) AS total_comments
    FROM comments
    GROUP BY author
    ORDER BY total_comments DESC
    LIMIT 10;
    """
)

conn.close()