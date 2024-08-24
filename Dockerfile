# Basis-Image setzen
FROM continuumio/miniconda3

# Arbeitsverzeichnis setzen
WORKDIR /app

# Kopieren Sie die environment.yml Datei
COPY environment.yml .

# Erstellen Sie die Conda-Umgebung
RUN conda config --set pip_interop_enabled True && \
    conda env create -f environment.yml

# Aktivieren Sie die Conda-Umgebung und legen Sie diese als Standard fest
RUN echo "source activate distributedcomputingenv" > ~/.bashrc
ENV PATH /opt/conda/envs/distributedcomputingenv/bin:$PATH

# System-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y build-essential libpq-dev ssh postgresql postgresql-contrib

# PostgreSQL-Konfiguration anpassen (als root)
USER root

# Anpassung der PostgreSQL-Konfigurationsdateien
RUN PGDATA=$(ls /etc/postgresql) && \
    echo "host all all 0.0.0.0/0 md5" >> /etc/postgresql/$PGDATA/main/pg_hba.conf && \
    echo "listen_addresses='*'" >> /etc/postgresql/$PGDATA/main/postgresql.conf

# PostgreSQL als Benutzer 'postgres' konfigurieren und starten
USER postgres
RUN service postgresql start && \
    psql --command "CREATE USER sep WITH SUPERUSER PASSWORD 'sep';" && \
    createdb -O sep distributed_computing

# Wieder zurück zum root-Benutzer wechseln
USER root

# App-Code kopieren
COPY Datenspeicherung/ /app/Datenspeicherung/

# PostgreSQL beim Start des Containers aktivieren
CMD service postgresql start && tail -f /dev/null
