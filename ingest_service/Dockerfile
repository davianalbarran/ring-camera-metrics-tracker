FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Tell Poetry not to create virtualenvs (important in Docker)
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_NO_INTERACTION=1

WORKDIR /app

# System deps (minimal)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       curl ca-certificates \
       git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy dependency files first (layer caching)
COPY pyproject.toml poetry.lock ./

# Install deps only (no source code yet)
RUN poetry install --no-root

# Copy the rest of the application
COPY *.py ./

# Run via poetry (or python directly — both work)
CMD ["poetry", "run", "python", "main.py"]