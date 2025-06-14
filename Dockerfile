FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create an admin user on first run
ARG ADMIN_USER=admin
ARG ADMIN_EMAIL=admin@example.com
ARG ADMIN_PASSWORD=admin

# Make sure the admin script is executable
RUN chmod +x create_admin.py

# Command to run at container startup
CMD python create_admin.py ${ADMIN_USER} ${ADMIN_EMAIL} ${ADMIN_PASSWORD} || echo "Admin already exists" && python main.py
