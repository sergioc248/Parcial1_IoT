FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY samples.ini .
COPY sender_live.py .
COPY sender_batch.py .
COPY devices/ ./devices/
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

CMD ["sh", "entrypoint.sh"]
