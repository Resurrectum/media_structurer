FROM python:3.10-slim

# Install system dependencies required for image processing libraries
RUN apt-get update && apt-get install -y \
    libimage-exiftool-perl \
    libmediainfo0v5 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Python dependencies and install them
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY main.py .
COPY imagetools.py .
COPY config.py .
COPY logger.py .

# Create directories for logs
RUN mkdir -p /app/logs

# Set environment variable to ensure Python output is sent straight to terminal
ENV PYTHONUNBUFFERED=1

# Run the main script
CMD ["python", "main.py"]
