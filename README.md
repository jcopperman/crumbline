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
- User authentication with secure login
- Session management with JWT tokens
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
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Create an admin user:
```bash
# Make sure to use the Python from the virtual environment
./venv/bin/python create_admin.py admin admin@example.com yourpassword
```

2. Start the server:
```bash
# Use the Python from the virtual environment
./venv/bin/python main.py
```

3. Open your browser and navigate to http://localhost:8000

4. Log in with the credentials you created

## Server Deployment

To deploy Crumbline on a production server with Nginx:

1. Clone the repository to your server:
```bash
git clone <repository-url> /var/www/crumbline
cd /var/www/crumbline
```

2. Run the automated setup script (requires root privileges):
```bash
sudo ./setup_server.sh
```

3. The script will:
   - Install necessary system packages
   - Create a Python virtual environment
   - Install Python dependencies
   - Create an admin user
   - Configure a systemd service for automatic startup
   - Configure Nginx as a reverse proxy
   - Set proper file permissions

4. Access your Crumbline instance at your domain.

### Manual Setup

If you prefer to set up manually:

1. Install Nginx and create a virtual environment
```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. Copy the systemd service file and enable it (make sure the paths in the service file point to your virtual environment):
```bash
sudo cp crumbline.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable crumbline.service
sudo systemctl start crumbline.service
```

3. Configure Nginx:
```bash
sudo cp nginx_crumbline.conf /etc/nginx/sites-available/crumbline
sudo ln -sf /etc/nginx/sites-available/crumbline /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Alternative: Using Supervisor (instead of systemd)

If you prefer using Supervisor instead of systemd:

1. Install Supervisor:
```bash
sudo apt install -y supervisor
```

2. Copy the supervisor configuration file:
```bash
sudo cp supervisor_crumbline.conf /etc/supervisor/conf.d/crumbline.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start crumbline
```

3. Check the status with:
```bash
sudo supervisorctl status crumbline
```

### Docker Deployment

For a containerized deployment using Docker:

1. Make sure Docker and Docker Compose are installed:
```bash
sudo apt update
sudo apt install -y docker.io docker-compose
```

2. Build and start the containers:
```bash
cd /var/www/crumbline
docker-compose up -d
```

3. Access Crumbline at http://your-server-ip:80

4. For security in production, edit the `docker-compose.yml` file to change:
   - The default admin password
   - The SECRET_KEY environment variable

5. To update the application:
```bash
git pull
docker-compose up -d --build
```

### Setting up SSL with Let's Encrypt

To secure your Crumbline instance with HTTPS:

1. Make sure you have a domain pointing to your server
2. Run the SSL setup script:

```bash
sudo ./setup_ssl.sh
```

3. The script will:
   - Install Certbot
   - Obtain SSL certificates for your domain
   - Configure Nginx to use HTTPS
   - Enable automatic certificate renewal

Alternatively, you can manually set up SSL:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

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