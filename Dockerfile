FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY IoTCentralSender.py .
COPY samples.ini .

CMD ["python", "IoTCentralSender.py"]
