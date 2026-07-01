# Design Notes — Part 6

## Q1 — Why did you structure your solution the way you did?

The pipeline is split into four components, each with a single responsibility. `YouTubeAPIClient` handles only HTTP communication with the YouTube API — it knows nothing about files or databases. `Ingestor` orchestrates the fetching process and saves the raw API response to disk before any cleaning happens; this "landing zone" means we can always re-run transformation without hitting the API again. `Transformer` reads that raw file and flattens it into clean, analysis-ready records — completely decoupled from how the data was fetched. Finally, `Storage` handles all database interaction. This separation makes each component easy to test, replace, or extend independently.

## Q2 — What would break at scale?

At 50,000 videos, three bottlenecks would emerge. First, the YouTube API quota (10,000 units/day) would be exhausted quickly — the solution is to implement request queuing with quota tracking and spread fetching across multiple days or API keys. Second, loading all video IDs into memory before fetching details would become a problem — switching to a streaming/batched approach (process N videos at a time) would fix this. Third, writing all records to SQLite in a single transaction would slow down significantly — PostgreSQL with bulk COPY operations and proper indexing on `channel_id` and `published_at` would handle this scale better.

## Q3 — What would you improve with more time?

The area I'm least satisfied with is comment fetching: for videos with disabled comments, the API returns a 403 error which is silently swallowed and logged as a warning. With more time, I would distinguish between "comments disabled" (expected, flag the video) and a genuine API error (should trigger a retry), and store that flag in the database so analysts know why comment_count is 0 for certain videos.