ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /app


FROM base AS dependencies
RUN python -m venv /opt/venv
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt


FROM dependencies AS dev
COPY requirements-dev.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements-dev.txt
COPY . .
CMD ["flask", "--app", "run:application", "run", "--debug", "--host", "0.0.0.0", "--port", "5000"]


FROM dev AS test
RUN python -m pytest -q -p no:cacheprovider


FROM base AS prod
ARG VERSION=dev
ARG REVISION=unknown
LABEL org.opencontainers.image.title="revoshop-api" \
    org.opencontainers.image.version=$VERSION \
    org.opencontainers.image.revision=$REVISION

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

COPY --from=dependencies /opt/venv /opt/venv
COPY --chown=app:app app ./app
COPY --chown=app:app config ./config
COPY --chown=app:app migrations ./migrations
COPY --chown=app:app run.py gunicorn.conf.py ./
ENV APP_ENV=production \
    FLASK_APP=run:application \
    PORT=5000 \
    WEB_CONCURRENCY=2 \
    LOG_TO_FILE=false 

USER 10001
EXPOSE 5000

HEALTHCHECK --interval=15s --timeout=3s --start-period=15s --retries=3 \
    CMD [ "python", "-c", "import os, urllib.request; urllib.request.urlopen(f\"http://127.0.0.1:{os.environ['PORT']}/api/v1/health/live\", timeout=2)"]

CMD ["gunicorn", "-c", "gunicorn.conf.py", "run:application"]
