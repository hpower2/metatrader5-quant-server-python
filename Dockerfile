FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md /workspace/
COPY app /workspace/app
COPY configs /workspace/configs
COPY docs /workspace/docs
COPY tests /workspace/tests

RUN python -m pip install --upgrade pip \
    && python -m pip install -e .[dev]

ENV APP_RUNS_ROOT=/mnt/shared/mt5/runs

CMD ["python", "-m", "app", "--help"]
