Dockerfile
# Verwenden Sie ein Basis-Image von Miniconda
FROM continuumio/miniconda3

# Setze das Arbeitsverzeichnis
WORKDIR /usr/src/app

# Installiere die notwendigen System-Bibliotheken und Build-Tools
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libarchive13 \
    libarchive-tools \
    libarchive-dev \
    build-essential \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/lib/x86_64-linux-gnu/libarchive.so.13 /usr/lib/x86_64-linux-gnu/libarchive.so.19

# Benutze den klassischen conda-Solver
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
RUN echo "Beginne mit der Umgebung-Aktualisierung..." && \
    mamba env update --file environment.yml --name myenv && \
    conda clean -afy && \
    echo "Umgebung aktualisiert mit environment.yml"

# Kopiere die Anwendung
COPY . .

# Verifikation durchlaufen lassen
RUN echo "Conda list post-init:" && conda list
RUN echo "Verifizierung Schritte:" && conda info

# Setze den Eintragspunkt
CMD ["python", "CapacityCheck/CapacityCheck.py"]
