FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libfreetype6 \
    libjpeg62-turbo \
    libopenjp2-7 \
    libtiff6 \
    libwebp7 \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*
# Install system Open Sans for Pillow font fallback
RUN mkdir -p /usr/share/fonts/truetype/open-sans && \
    apt-get update && apt-get install -y --no-install-recommends fonts-open-sans && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

ENV PORT=8000
ENV HOST=0.0.0.0

EXPOSE 8000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-keep-alive 120"]
