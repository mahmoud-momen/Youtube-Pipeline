"""
ingest.py

Orchestrates the ingestion process:
- uses a YouTubeAPIClient to fetch videos + comments for a list of channels
- saves the RAW (uncleaned) response to disk as the "landing zone",
  before any transformation happens (see transform.py for that step)

"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from api_client import YouTubeAPIClient

logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path("data/raw")


class Ingestor:
    """Coordinates fetching data for a set of channels and saving it raw."""

    def __init__(self, client: YouTubeAPIClient, videos_per_channel: int = 20, comments_per_video: int = 30):
        self.client = client
        self.videos_per_channel = videos_per_channel
        self.comments_per_video = comments_per_video
        RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    def run(self, channel_names: list[str]) -> Path:
        """
        Fetch videos + comments for every channel in channel_names,
        save the combined raw payload to a timestamped JSON file,
        and return the path to that file.
        """
        all_videos_raw = []

        for channel_name in channel_names:
            logger.info("Resolving channel: %s", channel_name)
            channel_id = self.client.get_channel_id_by_name(channel_name)
            if not channel_id:
                logger.warning("Skipping channel '%s' — could not resolve channel id.", channel_name)
                continue

            uploads_playlist_id = self.client.get_uploads_playlist_id(channel_id)
            if not uploads_playlist_id:
                logger.warning("Skipping channel '%s' — could not find uploads playlist.", channel_name)
                continue

            video_ids = self.client.get_video_ids_from_playlist(
                uploads_playlist_id, max_videos=self.videos_per_channel
            )
            logger.info("Found %s videos for channel '%s'", len(video_ids), channel_name)

            video_details = self.client.get_videos_details(video_ids)

            for video in video_details:
                video_id = video["id"]
                comments = self.client.get_comments_for_video(video_id, max_comments=self.comments_per_video)

                all_videos_raw.append({
                    "source_channel_query": channel_name,
                    "video_raw": video,       # untouched API response for this video
                    "comments_raw": comments,  # already a list of dicts (kept simple/raw)
                })

        output_path = self._save_raw(all_videos_raw)
        return output_path

    def _save_raw(self, data: list[dict]) -> Path:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        output_path = RAW_DATA_DIR / f"raw_videos_{timestamp}.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("Saved raw data for %s videos to %s", len(data), output_path)
        return output_path