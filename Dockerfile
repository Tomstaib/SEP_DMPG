# Basis-Image mit Miniconda von conda-forge
FROM condaforge/mambaforge:latest

# Arbeitsverzeichnis setzen
WORKDIR /app

# Anforderungen kopieren und installieren
COPY environment.yml .
RUN mamba env update --file environment.yml

# Anwendungscode kopieren
COPY . .

# Linting Schritt
RUN mamba run -n myenv flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
RUN mamba run -n myenv flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Test Schritt
RUN mamba run -n myenv pytest

# Startbefehl setzen (falls erforderlich)
CMD ["python", "main.py"]
