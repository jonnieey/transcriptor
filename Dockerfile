FROM python:3.12.7-slim-bookworm

ENV TRANS_ENV=development \
  # python:
  PYTHONFAULTHANDLER=1 \
  PYTHONUNBUFFERED=1 \
  PYTHONHASHSEED=random \
  PYTHONDONTWRITEBYTECODE=1 \
  # pip:
  PIP_NO_CACHE_DIR=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PIP_DEFAULT_TIMEOUT=100 \
  PIP_ROOT_USER_ACTION=ignore \
  # poetry:
  POETRY_VERSION=2.1.1 \
  POETRY_VIRTUALENVS_CREATE=false \
  POETRY_CACHE_DIR='/var/cache/pypoetry' \
  POETRY_HOME='/usr/local'

RUN apt-get update && apt-get upgrade -y \
  && apt-get install --no-install-recommends -y \
  bash \
  build-essential \
  curl \
  libpango1.0-dev \
  ffmpeg

RUN curl -sSL 'https://install.python-poetry.org' | python - \
  && poetry --version

WORKDIR /app
COPY . ./
RUN poetry lock && poetry install --no-interaction --no-ansi
