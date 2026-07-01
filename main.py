"""
main.py
Full pipeline: Ingest → Transform → Store
"""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from api_client import YouTubeAPIClient
from ingest import Ingestor
from transform import Transformer
from storage import Storage

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CHANNEL_NAMES = [
    "Podcast El Masyada",
    "في الضلمة In the dark",
    "SAMEH SANAD سامح سند",
]
VIDEOS_PER_CHANNEL = 20
COMMENTS_PER_VIDEO = 30


def main():
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        raise RuntimeError("YOUTUBE_API_KEY not found.")

    # Step 1: Ingest
    client = YouTubeAPIClient(api_key=api_key)
    ingestor = Ingestor(client=client, videos_per_channel=VIDEOS_PER_CHANNEL, comments_per_video=COMMENTS_PER_VIDEO)
    raw_path = ingestor.run(CHANNEL_NAMES)

    # Step 2: Transform
    transformer = Transformer()
    videos, comments = transformer.run(raw_path)

    # Step 3: Store
    db = Storage()
    db.load_videos(videos)
    db.load_comments(comments)
    db.close()
    logger.info("Pipeline complete. Database saved at: %s", "data/youtube_pipeline.db")


if __name__ == "__main__":
    main()