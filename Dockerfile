# Basis-Image setzen
FROM python:3.9-slim

# Arbeitsverzeichnis setzen
WORKDIR /app

# System-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y build-essential libpq-dev ssh

# Anforderungen installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code kopieren
COPY Datenspeicherung/ /app/Datenspeicherung/

# Container-Standardkommando
CMD ["python", "/app/Datenspeicherung/database_connection.py"]
