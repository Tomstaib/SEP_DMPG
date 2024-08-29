# Optimiertes Basis-Image von Miniconda verwenden.
FROM continuumio/miniconda3

# Setze das Arbeitsverzeichnis
WORKDIR /app

# Kopiere den gesamten Inhalt des aktuellen Verzeichnisses auf dem Host in das Arbeitsverzeichnis im Container
COPY . .

# Installiere notwendige System-Abhängigkeiten und Build-Tools
RUN apt-get update && apt-get install -y build-essential && apt-get clean

# Erstelle die Conda-Umgebung aus der environment.yml Datei
RUN conda env create -f environment.yml

# Aktivieren der Conda-Umgebung und Setzen als Standard
RUN echo "source activate my_env" >> ~/.bashrc && \
    echo "conda activate my_env" >> ~/.bashrc
ENV PATH /opt/conda/envs/my_env/bin:$PATH

# Füge das Arbeitsverzeichnis zum PYTHONPATH hinzu
ENV PYTHONPATH=/app

# Halte den Container aktiv und teste das Laden der Module mit einer kontinuierlichen Ausgabe
CMD ["bash", "-c", "while true; do echo 'Container is up and running'; python -c 'import SSHVerbindung.ssh_with_parameters; print(\"Module SSHVerbindung.ssh_with_parameters loaded successfully\")'; sleep 60; done"]