# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.13.1
FROM python:${PYTHON_VERSION}-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (for PostgreSQL, Pillow, OpenCV, pyzbar, etc.)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    libpng-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libzbar0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create media directory with proper permissions
RUN mkdir -p /app/media /app/staticfiles && \
    chmod -R 755 /app/media /app/staticfiles

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port (Railway will override this with PORT env var)
EXPOSE 8000

# Run migrations and start server
# Railway provides PORT environment variable
CMD python manage.py migrate && \
    gunicorn coopims.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 120
