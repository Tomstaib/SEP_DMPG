# Optimiertes Basis-Image von Miniconda verwenden
FROM continuumio/miniconda3

# Setze das Arbeitsverzeichnis
WORKDIR /usr/src/app

# Installiere notwendige System-Bibliotheken und Build-Tools
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libarchive-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/lib/x86_64-linux-gnu/libarchive.so.13 /usr/lib/x86_64-linux-gnu/libarchive.so.19

# Installiere Mamba und aktiviere es als Default-Paketmanager
RUN conda install mamba -n base -c conda-forge && conda clean -afy

# Erstelle eine Python 3.11 Umgebung mit Mamba
RUN mamba create -n myenv python=3.11 && conda clean -afy

# Setze die Umgebungsvariable, damit die Umgebung "myenv" verwendet wird
ENV PATH /opt/conda/envs/myenv/bin:$PATH

# Kopiere die environment.yml Datei ins Arbeitsverzeichnis
COPY environment.yml .

# Nutze Mamba für die Aktualisierung der Umgebung mit environment.yml
RUN mamba env update --file environment.yml --name myenv && conda clean -afy

# Kopiere die Anwendung
COPY . .

# Verifikation durchlaufen lassen (optional, kann entfernt werden, um Beschleunigung zu erhöhen)
RUN conda list && conda info

# Setze den Eintragspunkt
CMD ["python", "Kapazitätsprüfung/CapacityCheck.py"]
