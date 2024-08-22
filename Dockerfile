# Verwenden Sie ein Basis-Image von Miniconda
FROM continuumio/miniconda3:4.12.0

# Setze das Arbeitsverzeichnis
WORKDIR /usr/src/app

# Installiere die notwendigen System-Bibliotheken und Build-Tools
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libatlas-base-dev \
    libarchive13 \
    libarchive-tools \
    libarchive-dev \
    build-essential \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Benutze klassischen conda-Solver
RUN conda config --set solver classic

# Installiere Mamba
RUN conda install mamba -n base -c conda-forge && conda clean -afy && echo "Mamba installiert"

# Erstelle und aktiviere eine Python 3.11 Umgebung
RUN mamba create -n myenv python=3.11 && conda clean -afy && echo "Python 3.11 Umgebung erstellt"

# Setze die Umgebungsvariable, damit die Umgebung "myenv" verwendet wird
ENV PATH /opt/conda/envs/myenv/bin:$PATH

# Kopiere die environment.yml Datei ins Arbeitsverzeichnis
COPY environment.yml .

# Aktualisiere die Umgebung mit environment.yml
RUN mamba env update --file environment.yml --name myenv && conda clean -afy && echo "Umgebung aktualisiert mit environment.yml"

# Kopiere die requirements.txt Datei und entferne unsichtbare Zeichen
COPY requirements.txt .
RUN tr -cd '\11\12\15\40-\176' < requirements.txt > clean_requirements.txt && \
    echo "Inhalt von clean_requirements.txt:" && cat clean_requirements.txt

# Installiere zusätzliche pip-Abhängigkeiten
RUN echo "Beginne mit der Installation der pip-Abhängigkeiten..." && \
    pip install --no-cache-dir -r clean_requirements.txt || { \
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
