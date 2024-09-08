# Basierend auf dem offiziellen Logstash Image
FROM docker.elastic.co/logstash/logstash:7.10.1

# Festlegen der Conda Version und Installationspfad
ENV CONDA_DIR /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

# Installiere wget und bzip2, um Conda herunterzuladen und zu installieren
USER root
RUN apk add --no-cache wget bash bzip2 \
    && wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p /opt/conda \
    && rm /tmp/miniconda.sh \
    && /opt/conda/bin/conda init bash \
    && /opt/conda/bin/conda update -n base -c defaults conda \
    && apk del wget bzip2 \
    && rm -rf /var/cache/apk/*

# Kopiere die environment.yml (falls du zusätzliche Python-Abhängigkeiten hast)
COPY environment.yml /tmp/environment.yml

# Erstelle die Conda-Umgebung basierend auf environment.yml
RUN /opt/conda/bin/conda env create -f /tmp/environment.yml

# Aktiviere die Conda-Umgebung standardmäßig im Container
RUN echo "source activate myenv" >> ~/.bashrc

# Kopiere die Logstash-Konfigurationsdatei
COPY logstash.conf /usr/share/logstash/pipeline/logstash.conf

# Kopiere den gesamten Repository-Code ins Image
COPY . /usr/share/logstash/code

# Setze das Arbeitsverzeichnis auf das Verzeichnis mit deinem Code
WORKDIR /usr/share/logstash/code

# Exponiere die Ports, die von Logstash verwendet werden
EXPOSE 5044 9600

# Start-Command für Logstash
CMD ["logstash", "-f", "/usr/share/logstash/pipeline/logstash.conf"]
