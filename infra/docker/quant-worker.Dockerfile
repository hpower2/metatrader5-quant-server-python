FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md alembic.ini /app/
COPY apps /app/apps
COPY libs /app/libs
COPY migrations /app/migrations

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

CMD ["python", "-m", "apps.worker.main", "scheduler"]

