FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HOME=/home/app HF_HOME=/home/app/.cache/huggingface
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates libgomp1 && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 10001 app && mkdir -p /app/data /home/app/.cache/huggingface && chown -R app:app /app /home/app
COPY requirements.txt requirements-ai.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-ai.txt
COPY --chown=app:app backend ./backend
COPY --chown=app:app frontend ./frontend
USER app
FROM base AS backend
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
FROM base AS frontend
EXPOSE 8501
CMD ["streamlit", "run", "frontend/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true", "--browser.gatherUsageStats=false"]
