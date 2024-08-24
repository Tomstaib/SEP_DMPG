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

# System-Abhängigkeiten installieren
RUN apt-get update && apt-get install -y build-essential libpq-dev ssh postgresql postgresql-contrib nano

# PostgreSQL-Konfiguration anpassen
# Zuerst root sein, um die Config-Anpassungen durchzuführen
USER root

# Script für die PostgreSQL-Konfiguration erstellen und ausführen
RUN bash -c 'PGDATA=$(ls /etc/postgresql) && \
    echo "host all all 0.0.0.0/0 md5" >> /etc/postgresql/$PGDATA/main/pg_hba.conf && \
    echo "listen_addresses=\'*\'" >> /etc/postgresql/$PGDATA/main/postgresql.conf'

# PostgreSQL als Benutzer 'postgres' konfigurieren
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
