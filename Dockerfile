# syntax=docker/dockerfile:1
ARG PYTHON_VERSION=3.13.1
FROM python:${PYTHON_VERSION}-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

ARG UID=10001
RUN adduser \
    --disabled-password \
    --gecos "" \
    --home "/nonexistent" \
    --shell "/sbin/nologin" \
    --no-create-home \
    --uid "${UID}" \
    appuser

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=bind,source=requirements.txt,target=requirements.txt \
    python -m pip install --upgrade pip && \
    python -m pip install -r requirements.txt

# Copy project files
COPY . .

# --- NEW: Collect static files ---
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run the app with Gunicorn
CMD gunicorn coopims.wsgi:application --bind 0.0.0.0:8000
