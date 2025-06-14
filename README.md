# Crumbline

A simple, self-hosted RSS feed reader built with FastAPI, HTMX, and Tailwind CSS.

## Why Crumbline?

I built this out of pure frustration.  
Netvibes nuked my years-old RSS dashboard — a quiet place where I followed webcomics, poetry, and scattered corners of the internet.  
Instead of settling for whatever bloated or ad-ridden replacement came next, I built my own.  
Now I control it, I host it, and it'll never disappear unless I decide it does.

## Features

- Add and remove RSS feeds
- Group feeds into categories
- Automatic feed updates every 30 minutes
- Mark entries as read/unread
- Clean, responsive UI with Tailwind CSS
- Dynamic updates with HTMX

## Requirements

- Python 3.8+
- SQLite3

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd crumbline
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the server:
```bash
python main.py
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

3. Add your first RSS feed by entering its URL in the sidebar form.

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application and routes
│   ├── models.py        # SQLAlchemy models
│   ├── database.py      # Database connection
│   └── services.py      # Feed handling services
├── templates/
│   ├── base.html        # Base template
│   ├── index.html       # Main page template
│   ├── feed_item.html   # Feed list item template
│   ├── feed_entry.html  # Feed entry template
│   └── feed_entries.html # Feed entries container
├── static/             # Static files (if any)
├── main.py             # Application entry point
├── requirements.txt    # Python dependencies
└── feeds.db           # SQLite database (created automatically)
```

## Development

The application uses:
- FastAPI for the backend API
- SQLAlchemy for database operations
- HTMX for dynamic updates
- Tailwind CSS for styling
- APScheduler for background feed updates

## License

MIT

---

If you want I can also add a small `crontab` or `systemd` guide later. Let me know when you're ready to open-source it or link it up to the domain.