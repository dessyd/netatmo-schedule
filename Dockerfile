FROM python:3.9-slim

WORKDIR /app

# Install required packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY netatmo_otel/ /app/netatmo_otel/

# Setup cron for scheduled execution
RUN apt-get update && apt-get -y install cron
COPY crontab /etc/cron.d/netatmo-cron
RUN chmod 0644 /etc/cron.d/netatmo-cron
RUN crontab /etc/cron.d/netatmo-cron

# Create volume mount points for persistent data
RUN mkdir -p /app/data
VOLUME /app/data

# Create empty .env file if not mounted
RUN touch /app/.env

# Start cron in foreground
CMD ["cron", "-f"]