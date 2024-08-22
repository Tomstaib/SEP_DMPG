# Verwenden Sie ein Basis-Image von Miniconda
FROM continuumio/miniconda3:4.12.0

# Setze das Arbeitsverzeichnis
WORKDIR /usr/src/app

# Installiere die notwendigen System-Bibliotheken
RUN apt-get update && apt-get install -y libarchive13 && rm -rf /var/lib/apt/lists/*

# Installiere Mamba
RUN conda install mamba -n base -c conda-forge && conda clean -afy && echo "Mamba installiert"

# Erstelle und aktiviere eine Python 3.11 Umgebung
RUN mamba create -n myenv python=3.11 && conda clean -afy && echo "Python 3.11 Umgebung erstellt"

# Setze die Umgebungsvariable, damit die Umgebung "myenv" verwendet wird
ENV PATH /opt/conda/envs/myenv/bin:$PATH

# Kopiere die environment.yml und requirements.txt Datei ins Arbeitsverzeichnis
COPY environment.yml .
COPY requirements.txt .

# Aktualisiere die Umgebung mit environment.yml
RUN mamba env update --file environment.yml --name myenv && conda clean -afy && echo "Umgebung aktualisiert mit environment.yml"

# Installiere pip-Abhängigkeiten aus der requirements.txt in der conda Umgebung
RUN pip install --no-cache-dir -r requirements.txt || { \
    echo "Fehler bei der Installation von pip-Abhängigkeiten"; \
    exit 1; \
}

# Kopiere die Anwendung
COPY . .

# Verifikation durchlaufen lassen
RUN echo "Conda list post-init" && conda list
RUN echo "Verifizierung Schritte" && conda info

# Setze den Eintragspunkt
CMD ["python", "CapacityCheck/CapacityCheck.py"]
