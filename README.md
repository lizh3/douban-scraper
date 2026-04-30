# douban-scraper

Export your Douban reviews, ratings, and comments to JSON.

A command line tool that pulls your public Douban data through their mobile APIs. No browser automation, no Selenium, no login required for most data.

## Features

- **Movies, books, music** via the Frodo API (no authentication needed)
- **Broadcasts** (广播/miniblog) via the Rexxar API (requires a cookie)
- **Resumable** scraping with a `.progress.json` file. If it gets interrupted, just run the same command again and it picks up where it left off
- **No login needed** for public profile data (movies, books, music)

## Limitations

Be aware of what this tool does **not** do:

- **Long-form reviews (评论/影评) are NOT supported.** There is no API endpoint for them, and Douban's web pages are protected by proof-of-work challenges that block automated scraping. This is not a bug, it is a hard limitation.
- **Game collections** are not supported in v1.
- **Private profile data** requires additional work and is not yet implemented.

## Installation

```bash
pip install -e .
```

For development (includes pytest, ruff):

```bash
pip install -e ".[dev]"
```

Requires Python 3.10 or later.

## Quick Start

```bash
douban-scraper export --user YOUR_UID --types movie,book,music --output ./my-data
```

This fetches all your movie, book, and music ratings and saves them as JSON files in `./my-data/`.

## Authentication

### Movies, books, music (no auth needed)

The tool uses the Frodo mobile API with a built-in API key and HMAC-SHA1 signature. You do not need to log in or provide any credentials for public profile data.

### Broadcasts (cookie required)

Broadcasts go through the Rexxar API, which requires a valid `ck` cookie from an authenticated browser session.

```bash
douban-scraper export --user YOUR_UID --types broadcast --cookie "ck=YOUR_CK_VALUE" --output ./my-data
```

## Finding Your User ID

Your Douban User ID is the numeric part of your profile URL.

Open your Douban profile page. The URL looks like:

```
https://www.douban.com/people/123456789/
```

The number `123456789` is your User ID. Pass it with `--user 123456789`.

## Getting the Cookie for Broadcasts

1. Log in to Douban in your browser
2. Open Developer Tools (F12 or Ctrl+Shift+I)
3. Go to the **Application** tab (Chrome) or **Storage** tab (Firefox)
4. Under **Cookies**, find `m.douban.com`
5. Copy the value of the cookie named `ck`
6. Pass it as `--cookie "ck=YOUR_VALUE"`

## Output Format

The tool writes one JSON file per type to the output directory:

- `movie_{status}.json`
- `book_{status}.json`
- `music_{status}.json`
- `broadcast.json`

A progress file (`.progress.json`) tracks what has been scraped so far.

Each file contains a JSON array of items. Here is what a single movie entry looks like:

```json
{
  "comment": "Rewatched this again, still holds up.",
  "rating": {
    "value": 5,
    "max": 5
  },
  "create_time": "2024-08-12 22:31:17",
  "subject": {
    "id": "35290178",
    "title": "奥本海默",
    "url": "https://movie.douban.com/subject/35290178/",
    "cover": "https://img2.doubanio.com/view/photo/s_ratio_poster/public/p2895451952.jpg",
    "rating": {
      "value": 8.9
    },
    "type": "movie",
    "year": "2023",
    "card_subtitle": "2023 / 美国 英国 / 剧情 传记 历史 / 克里斯托弗·诺兰 / 基里安·墨菲 艾米莉·布朗特"
  },
  "status": "done",
  "tags": ["诺兰", "历史", "2023"]
}
```

Broadcast items have a different shape:

```json
{
  "id": "abc123",
  "text": "Just finished reading this. Highly recommended.",
  "created_at": "2024-07-20 14:05:00",
  "comments_count": 3,
  "likes_count": 12,
  "subject": null,
  "reshared_status": null
}
```

## Configuration Flags

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--user` | Yes | | Your Douban User ID (numeric) |
| `--types` | Yes | | Comma-separated list: `movie`, `book`, `music`, `broadcast` |
| `--status` | No | `done` | Interest status to fetch: `done`, `mark`, `doing`, `onhold`, `dropped` |
| `--output` | No | `./output` | Directory to write JSON files to |
| `--cookie` | For broadcasts | | Cookie string for authenticated endpoints, e.g. `ck=XXX` |
| `--delay` | No | `1.0` | Seconds to wait between API requests |
| `--max-items` | No | `0` | Max items to fetch per type (0 means all) |
| `--api-key` | No | built-in | Override the default Frodo API key |
| `--api-secret` | No | built-in | Override the default HMAC secret |
| `--force` | No | `false` | Re-scrape even if progress says completed |

## Development

```bash
pip install -e ".[dev]"
pytest
```
