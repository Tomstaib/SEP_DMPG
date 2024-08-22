# Verwenden Sie ein Basis-Image von Miniconda
FROM continuumio/miniconda3

# Setze das Arbeitsverzeichnis
WORKDIR /usr/src/app

# Kopiere die environment.yml und requirements.txt Datei ins Arbeitsverzeichnis
COPY environment.yml .
COPY requirements.txt .

# Installiere Mamba
RUN conda install mamba -n base -c conda-forge && conda clean -afy && echo "Mamba installiert"

# Aktualisiere die Umgebung mit environment.yml
RUN mamba env update --file environment.yml --name base && conda clean -afy && echo "Umgebung aktualisiert mit environment.yml"

# Installiere pip in der conda Umgebung
RUN mamba install --name base pip && conda clean -afy && echo "pip installiert"

# Kopieren Sie Ihre Anwendung
COPY . .

# Ausgabe der `requirements.txt` zum Debuggen
RUN echo "Inhalt von requirements.txt:" && cat requirements.txt

# Installiere pip-Abhängigkeiten aus requirements.txt
RUN pip install --no-cache-dir -r requirements.txt || { \
    echo "Fehler bei der Installation von pip-Abhängigkeiten"; \
    exit 1; \
}

# Verifikation durchlaufen lassen
RUN echo "Conda list post-init" && conda list
RUN echo "Verifizierung Schritte" && conda info

# Setze den Eintragspunkt
CMD ["python", "CapacityCheck/CapacityCheck.py"]
