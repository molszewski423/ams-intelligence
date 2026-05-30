FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY vault/ ./vault/
COPY README.md .

# Placeholder dirs — production paths are volume-mounted over these
RUN mkdir -p chroma_db output .streamlit \
    data/nhsn data/whonet data/atlas

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV OLLAMA_BASE_URL=http://ollama:11434

EXPOSE 8502

CMD ["streamlit", "run", "src/dashboard/app.py", \
     "--server.port=8502", "--server.address=0.0.0.0", \
     "--server.headless=true"]
