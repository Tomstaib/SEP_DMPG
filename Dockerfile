# Basierend auf dem offiziellen Logstash Image
FROM docker.elastic.co/logstash/logstash:7.10.1

USER root

# Installiere wget, bzip2 und andere Abhängigkeiten für die Conda-Installation
RUN apt-get update && apt-get install -y wget bzip2 \
    && wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p /opt/conda \
    && rm /tmp/miniconda.sh \
    && /opt/conda/bin/conda init bash \
    && /opt/conda/bin/conda update -n base -c defaults conda \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Festlegen der Conda Version und Installationspfad
ENV CONDA_DIR /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

# Kopiere die environment.yml (falls du zusätzliche Python-Abhängigkeiten hast)
COPY environment.yml /tmp/environment.yml

# Erstelle die Conda-Umgebung basierend auf environment.yml
RUN /opt/conda/bin/conda env create -f /tmp/environment.yml

# Aktiviere die Conda-Umgebung standardmäßig im Container
RUN echo "source activate myenv" >> ~/.bashrc

# Kopiere die Logstash-Konfigurationsdatei
COPY logstash.conf /usr/share/logstash/pipeline/logstash.conf

# Installiere Logstash-Plugins (falls notwendig)
# COPY die Plugins-Definitionen und installiere sie
# RUN /usr/share/logstash/bin/logstash-plugin install --local /usr/share/logstash/config/environment.yml

# Kopiere den gesamten Repository-Code ins Image
COPY . /usr/share/logstash/code

# Setze das Arbeitsverzeichnis auf das Verzeichnis mit deinem Code
WORKDIR /usr/share/logstash/code

# Exponiere die Ports, die von Logstash verwendet werden
EXPOSE 5044 9600

# Start-Command für Logstash
CMD ["logstash", "-f", "/usr/share/logstash/pipeline/logstash.conf"]
