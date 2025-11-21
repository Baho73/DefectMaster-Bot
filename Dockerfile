FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create volume for database
VOLUME ["/app/data"]

# Set environment variables
ENV DATABASE_PATH=/app/data/bot.db
ENV PYTHONUNBUFFERED=1

# Run bot
CMD ["python", "main.py"]
