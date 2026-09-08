FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Ensure start script is executable
RUN chmod +x /app/start.sh

# Ensure data directory exists
RUN mkdir -p /app/data/chroma_db

# Run the boot script
CMD ["/app/start.sh"]
