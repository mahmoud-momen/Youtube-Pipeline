"""
api_client.py

Responsible ONLY for talking to the YouTube Data API v3:
- building requests
- handling HTTP errors (timeouts, non-200 responses) gracefully
- returning raw parsed JSON (no cleaning/transformation happens here)
"""

import requests
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://www.googleapis.com/youtube/v3"


class YouTubeAPIClient:
    """Thin wrapper around the YouTube Data API v3 REST endpoints."""

    def __init__(self, api_key: str, timeout: int = 10, max_retries: int = 2):
        if not api_key:
            raise ValueError("An API key is required to create a YouTubeAPIClient.")
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()

    # ------------------------------------------------------------------
    # Low-level request helper (all other methods funnel through this)
    # ------------------------------------------------------------------
    def _get(self, endpoint: str, params: dict) -> dict | None:
        """
        Perform a GET request against the given endpoint.
        Returns the parsed JSON dict on success, or None on failure
        (after retries) so a single bad request never crashes the run.
        """
        url = f"{BASE_URL}/{endpoint}"
        params = {**params, "key": self.api_key}

        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(
                        "Non-200 response (%s) from %s on attempt %s/%s: %s",
                        response.status_code, endpoint, attempt, self.max_retries,
                        response.text[:200],
                    )
            except requests.exceptions.Timeout:
                logger.warning("Timeout calling %s (attempt %s/%s)", endpoint, attempt, self.max_retries)
            except requests.exceptions.RequestException as e:
                logger.warning("Request error calling %s (attempt %s/%s): %s", endpoint, attempt, self.max_retries, e)

            time.sleep(1.5 * attempt)  # simple backoff before retrying

        logger.error("Giving up on %s after %s attempts.", endpoint, self.max_retries)
        return None

    # ------------------------------------------------------------------
    # Public API methods
    # ------------------------------------------------------------------
    def get_channel_id_by_name(self, channel_name: str) -> str | None:
        """Resolve a human-readable channel name to its channelId via search."""
        data = self._get("search", {
            "part": "snippet",
            "q": channel_name,
            "type": "channel",
            "maxResults": 1,
        })
        if not data or not data.get("items"):
            logger.error("Could not resolve channel id for '%s'", channel_name)
            return None
        return data["items"][0]["snippet"]["channelId"]

    def get_uploads_playlist_id(self, channel_id: str) -> str | None:
        """Every channel has a hidden 'uploads' playlist; we need its id to list videos."""
        data = self._get("channels", {
            "part": "contentDetails",
            "id": channel_id,
        })
        if not data or not data.get("items"):
            return None
        return data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    def get_video_ids_from_playlist(self, playlist_id: str, max_videos: int = 20) -> list[str]:
        """Page through a playlist's items to collect video ids, up to max_videos."""
        video_ids = []
        page_token = None

        while len(video_ids) < max_videos:
            data = self._get("playlistItems", {
                "part": "contentDetails",
                "playlistId": playlist_id,
                "maxResults": min(50, max_videos - len(video_ids)),
                "pageToken": page_token,
            })
            if not data:
                break

            for item in data.get("items", []):
                video_ids.append(item["contentDetails"]["videoId"])

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return video_ids[:max_videos]

    def get_videos_details(self, video_ids: list[str]) -> list[dict]:
        """
        Fetch snippet + statistics for up to 50 video ids per call
        (the API allows batching ids, comma-separated, up to 50 at a time).
        """
        all_items = []
        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i:i + 50]
            data = self._get("videos", {
                "part": "snippet,statistics",
                "id": ",".join(chunk),
            })
            if data:
                all_items.extend(data.get("items", []))
        return all_items

    def get_comments_for_video(self, video_id: str, max_comments: int = 50) -> list[dict]:
        """
        Fetch top-level comments for a video.
        Returns an empty list (not an error) if comments are disabled,
        since that's a normal, expected state for some videos.
        """
        comments = []
        page_token = None

        while len(comments) < max_comments:
            data = self._get("commentThreads", {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": min(50, max_comments - len(comments)),
                "pageToken": page_token,
                "textFormat": "plainText",
            })
            if not data:
                # Either an error, or comments are disabled for this video (403).
                # Either way, we just return what we have (possibly empty).
                break

            for item in data.get("items", []):
                top_comment = item["snippet"]["topLevelComment"]["snippet"]
                comments.append({
                    "author": top_comment.get("authorDisplayName"),
                    "text": top_comment.get("textDisplay"),
                    "published_at": top_comment.get("publishedAt"),
                })

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        return comments