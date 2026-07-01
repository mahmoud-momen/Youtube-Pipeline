"""
transform.py
Cleans and flattens raw YouTube API data.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROCESSED_DATA_DIR = Path("data/processed")


class Transformer:

    def __init__(self):
        PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    def run(self, raw_path: Path) -> tuple:
        logger.info("Loading raw data from %s", raw_path)
        with open(raw_path, encoding="utf-8") as f:
            raw_data = json.load(f)

        videos = []
        comments = []

        for entry in raw_data:
            video = self._transform_video(entry)
            if video is None:
                continue
            videos.append(video)
            for comment in self._transform_comments(entry, video["video_id"]):
                comments.append(comment)

        self._save_processed(videos, comments, raw_path.stem)
        logger.info("Transformation complete: %s videos, %s comments", len(videos), len(comments))
        return videos, comments

    def _safe_int(self, value, default=0) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _transform_video(self, entry: dict):
        video_raw = entry.get("video_raw", {})
        snippet = video_raw.get("snippet", {})
        statistics = video_raw.get("statistics", {})
        video_id = video_raw.get("id")
        if not video_id:
            return None
        return {
            "video_id":      video_id,
            "title":         snippet.get("title", "").strip() or "Unknown Title",
            "channel_name":  snippet.get("channelTitle", "").strip() or entry.get("source_channel_query", "Unknown"),
            "channel_id":    snippet.get("channelId", ""),
            "published_at":  snippet.get("publishedAt", ""),
            "description":   snippet.get("description", "")[:500],
            "view_count":    self._safe_int(statistics.get("viewCount")),
            "like_count":    self._safe_int(statistics.get("likeCount")),
            "comment_count": self._safe_int(statistics.get("commentCount")),
        }

    def _transform_comments(self, entry: dict, video_id: str) -> list:
        comments_raw = entry.get("comments_raw", [])
        if not comments_raw:
            return []
        clean = []
        for c in comments_raw:
            text = (c.get("text") or "").strip()
            if not text:
                continue
            clean.append({
                "video_id":     video_id,
                "author":       (c.get("author") or "Anonymous").strip(),
                "text":         text[:1000],
                "published_at": c.get("published_at", ""),
            })
        return clean

    def _save_processed(self, videos: list, comments: list, stem: str):
        out = PROCESSED_DATA_DIR / f"processed_{stem}.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump({"videos": videos, "comments": comments}, f, ensure_ascii=False, indent=2)
        logger.info("Saved processed data to %s", out)