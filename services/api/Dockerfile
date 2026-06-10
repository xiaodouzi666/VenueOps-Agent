FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends curl ca-certificates nodejs npm \
  && rm -rf /var/lib/apt/lists/*

COPY services/api ./services/api
COPY data ./data

WORKDIR /app/services/api
RUN pip install --no-cache-dir -e ".[mcp]"

ENV PORT=8080
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
