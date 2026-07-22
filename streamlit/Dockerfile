FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:${PATH}" \
    CATALOG_DATA_MODE=fake \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

ARG DATACATALOG_DATABASE_NAME=FAKE_DATACATALOG
ENV DATACATALOG_DATABASE_NAME=${DATACATALOG_DATABASE_NAME}

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN sed "s/\${DATACATALOG_DATABASE_NAME}/${DATACATALOG_DATABASE_NAME}/g" \
    settings.py.template > settings.py

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
