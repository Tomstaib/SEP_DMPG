# Basis-Image setzen
FROM continuumio/miniconda3

# Arbeitsverzeichnis setzen
WORKDIR /app

# Kopieren Sie die environment.yml Datei
COPY environment.yml .

# Erstellen Sie die Conda-Umgebung
RUN conda env create -f environment.yml

# Aktivieren Sie die Conda-Umgebung und legen Sie diese als Standard fest
RUN echo "source activate distributed_computing_env" > ~/.bashrc
ENV PATH /opt/conda/envs/distributed_computing_env/bin:$PATH

# App-Code kopieren
COPY Datenspeicherung/ /app/Datenspeicherung/

# Container-Standardkommando
CMD ["python", "/app/Datenspeicherung/database_connection.py"]
