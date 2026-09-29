FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY investor_app/ .

RUN useradd --create-home appuser && chown appuser /app
USER appuser

EXPOSE 8000
# Development server; see docker-compose.yml for the worker and beat commands.
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
