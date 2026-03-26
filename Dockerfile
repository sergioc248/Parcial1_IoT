FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY samples.ini .
COPY IoTCentralSender_EstacionClimaExterno.py .
COPY "IoTCentralSenderBatch_EstacionClimaExterno..py" .
COPY IoTCentralSender_CultivoCacao.py .
COPY IoTCentralSenderBatch_CultivoCacao.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

CMD ["sh", "entrypoint.sh"]
