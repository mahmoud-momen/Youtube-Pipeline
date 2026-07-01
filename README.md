# YouTube Pipeline — Junior Data Engineer Assessment

A data pipeline that pulls data from the YouTube Data API v3 for three Arabic true-crime podcast channels, cleans it, and stores it in a SQLite database ready for analysis.

## Channels Covered
- Podcast El Masyada
- في الضلمة - In the dark
- SAMEH SANAD سامح سند

## Project Structure
youtube-pipeline/
├── api_client.py       # YouTubeAPIClient: handles all HTTP calls to YouTube API
├── ingest.py           # Ingestor: orchestrates fetching and saves raw JSON
├── transform.py        # Transformer: cleans and flattens raw data
├── storage.py          # Storage: creates SQLite schema and loads data
├── main.py             # Entry point — runs the full pipeline
├── queries.py          # Analytical queries against the database
├── design_notes.md     # Answers to Part 6 design questions
├── data.ipynb          # Data wrangling and visualizations
├── architecture_diagram.png
├── requirements.txt
├── .env.example
└── data/
├── raw/            # Landing zone: raw API responses (JSON)
├── processed/      # Transformed data (JSON)
├── csv/            # Exported CSVs for analysis
└── youtube_pipeline.db  # SQLite database

## Setup

### 1. Clone the repo and create a virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Mac/Linux
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your API key
Copy `.env.example` to `.env` and add your YouTube Data API v3 key: 
YOUTUBE_API_KEY=your_api_key_here


### 4. Run the pipeline
```bash
python main.py
```
This will:
- Fetch 60 videos (20 per channel) + up to 30 comments per video
- Save raw JSON to `data/raw/`
- Clean and flatten data to `data/processed/`
- Load everything into `data/youtube_pipeline.db`

### 5. Run analytical queries
```bash
python queries.py
```

## Storage Choice — Why SQLite?

The data has a clear relational structure: each video belongs to one channel, and each comment belongs to one video. This one-to-many relationship is a natural fit for SQL. SQLite was chosen over PostgreSQL because it requires no server setup and runs from a single file, making the pipeline easy to run and share. MongoDB would be a better choice if the schema were unpredictable or if comments had deeply nested, variable structure — but since we flatten everything in the transformation step, a document store offers no advantage here. If this pipeline needed to scale to hundreds of thousands of videos with concurrent writes, PostgreSQL would be the right upgrade.

## Analytical Queries & Results

### Query 1: Top 5 Videos by View Count
| Title | Channel | Views | Likes | Comments |
|-------|---------|-------|-------|----------|
| ٣ بلاغات \| تفكير شياطين \| جريمة العبور | SAMEH SANAD | 1,405,427 | 39,048 | 2,343 |
| الوش التاني جريمة بنغازي | SAMEH SANAD | 1,250,762 | 38,577 | 2,702 |
| منى و الكوارع | SAMEH SANAD | 1,161,694 | 35,514 | 2,434 |
| إيمان شيطانة عين شمس | SAMEH SANAD | 1,157,934 | 34,966 | 1,512 |
| أرنب .. حكاية من العالم الموازي | SAMEH SANAD | 1,090,918 | 35,241 | 1,659 |

### Query 2: Average Engagement per Channel
| Channel | Videos | Avg Views | Avg Likes | Avg Comments |
|---------|--------|-----------|-----------|--------------|
| SAMEH SANAD سامح سند | 20 | 486,302 | 16,027 | 804 |
| في الضلمة - In the dark | 20 | 292,055 | 12,323 | 719 |
| Podcast El Masyada | 20 | 96,454 | 3,544 | 578 |

### Query 3: Top 10 Most Active Commenters
| Author | Total Comments |
|--------|---------------|
| @ابراهيمعبده-د3ل5ي | 72 |
| @omnia-j1r8w | 27 |
| @algerie0742 | 24 |
| @EmanEbrhim-j9e | 24 |
| @BosbosAhmed1994 | 24 |
| @اليافعيةآلناجي | 21 |
| @user-cw7il7ov7k | 21 |
| @soadmohamed2082 | 21 |
| @razanrahil8741 | 21 |
| @Rokia-m8g | 21 |


<img width="1536" height="1024" alt="diagram" src="https://github.com/user-attachments/assets/e47296d7-7dce-4cb8-9697-41214252c48c" />

