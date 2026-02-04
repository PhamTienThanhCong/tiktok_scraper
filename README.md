# TikTok Scraper

A tool to scrape and download TikTok videos without watermark.

## Features

- Crawl video list from TikTok channels
- Filter videos by minimum views and likes
- Download HD videos without watermark
- Checkpoint support to resume interrupted downloads
- Save video statistics (views, likes, comments, shares)

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install requests yt-dlp
```

## Configuration

Edit [config.py](config.py):

```python
CHANNEL = "tiktok_username"  # TikTok channel name (without @)
MIN_PLAYS = 100000           # Minimum views (0 = no filter)
MIN_LIKES = 1000             # Minimum likes (0 = no filter)
```

## Usage

```bash
python main.py
```

### Main Menu

1. **Crawl videos** - Fetch video list from channel, save to `data/{channel}.json`
2. **Download videos** - Download HD videos without watermark to `videos_download/{channel}/videos/`
3. **Configuration** - Change channel, min views, min likes

## Directory Structure

```
tiktok_demo/
├── main.py                 # Entry point
├── config.py               # Configuration
├── tiktok_scraper/
│   ├── __init__.py
│   └── scraper.py          # TikTokScraper class
├── data/                   # Video list JSON files
└── videos_download/        # Downloaded videos
    └── {channel}/
        ├── videos/         # Video files (.mp4)
        ├── checkpoint.json # List of downloaded video IDs
        └── fail_videos.json # List of failed downloads
```

## API

### TikTokScraper

```python
from tiktok_scraper import TikTokScraper

# Initialize
scraper = TikTokScraper(
    profile_url="https://www.tiktok.com/@username",
    min_plays=100000,
    min_likes=1000
)

# Crawl videos
scraper.fetch_videos()

# Print summary
scraper.print_summary()

# Save to JSON
scraper.save_to_json("output.json")

# Download videos (no watermark, HD quality)
scraper.download_videos_via_api(base_dir="videos_download/username")
```

## Dependencies

- Python 3.12+
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Fetch video metadata
- [requests](https://requests.readthedocs.io/) - Download videos via API

## Notes

- Videos are downloaded via [tikwm.com](https://www.tikwm.com/) API to get watermark-free versions
- Checkpoint is saved after each video, allowing resume on interruption
- Failed downloads are logged to `fail_videos.json` for later retry
