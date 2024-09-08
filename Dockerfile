# Basierend auf dem offiziellen Logstash Image
FROM docker.elastic.co/logstash/logstash:7.10.1

# Festlegen der Conda Version und Installationspfad
ENV CONDA_DIR /opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

# Installiere wget und weitere Abhängigkeiten für die Conda-Installation
USER root
RUN apt-get update && apt-get install -y wget bzip2 \
    && wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh \
    && bash /tmp/miniconda.sh -b -p $CONDA_DIR \
    && rm /tmp/miniconda.sh \
    && conda init bash \
    && conda update -n base -c defaults conda \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Kopiere die environment.yml (falls du zusätzliche Python-Abhängigkeiten hast)
COPY environment.yml /tmp/environment.yml

# Erstelle die Conda-Umgebung basierend auf environment.yml
RUN conda env create -f /tmp/environment.yml

# Aktiviere die Conda-Umgebung standardmäßig im Container
RUN echo "source activate myenv" >> ~/.bashrc

# Kopiere die Logstash-Konfigurationsdatei
COPY logstash.conf /usr/share/logstash/pipeline/logstash.conf

# Kopiere die requirements.yml für Logstash Plugins (optional)
COPY requirements.yml /usr/share/logstash/config/requirements.yml

# Installiere Logstash-Plugins (optional)
RUN /usr/share/logstash/bin/logstash-plugin install --local < /usr/share/logstash/config/requirements.yml

# Kopiere den gesamten Repository-Code ins Image
COPY . /usr/share/logstash/code

# Setze das Arbeitsverzeichnis auf das Verzeichnis mit deinem Code
WORKDIR /usr/share/logstash/code

# Exponiere die Ports, die von Logstash verwendet werden
EXPOSE 5044 9600

# Start-Command für Logstash und optional Python-Skripte
CMD ["logstash", "-f", "/usr/share/logstash/pipeline/logstash.conf"]
