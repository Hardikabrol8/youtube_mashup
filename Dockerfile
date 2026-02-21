FROM python:3.11-slim

# Install FFmpeg and clean apt cache to keep image small
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose server port
EXPOSE 5000

# Run Flask using the Waitress WSGI production server
CMD ["python", "-m", "waitress", "--port=5000", "app:app"]
