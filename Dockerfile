# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    curl \
    ffmpeg \
    git \
    wget \
    jq \
    procps \
    python3-dev \
    calibre && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install Python dependencies from the requirements file and gunicorn
RUN pip install --no-cache-dir -r requirements.txt \
    gunicorn==20.1.0


# Copy the entire application code to the container
COPY . .

# Expose the port on which the web app will run (for gunicorn)
EXPOSE 8000

# Run both gunicorn for the web app and the lncrawl bot using telegram
CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:8000 & python3 pytest.py"]
