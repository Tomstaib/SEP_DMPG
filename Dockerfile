# Basis-Image mit Python und Conda
FROM continuumio/miniconda3

# Arbeitsverzeichnis setzen
WORKDIR /app

# Anforderungen kopieren und installieren
COPY environment.yml .
RUN conda env update --file environment.yml

# Dependencies Installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Anwendungscode kopieren
COPY . .

# Linting Schritt
RUN conda run -n base flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
RUN conda run -n base flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Test Schritt
RUN conda run -n base pytest

# Startbefehl setzen (falls erforderlich)
CMD ["python", "main.py"]
