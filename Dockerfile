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

# Aktivieren der Conda-Umgebung und als Standard festlegen
RUN echo "source activate my_env" >> ~/.bashrc && \
    echo "conda activate my_env" >> ~/.bashrc
ENV PATH=/opt/conda/envs/my_env/bin:$PATH

# Füge das Arbeitsverzeichnis und das Modulverzeichnis zum PYTHONPATH hinzu
ENV PYTHONPATH=/app:/app/SSHVerbindung

# Debugging: Ausgabe der Verzeichnisstruktur zur Überprüfung
RUN echo "Listing /app directory:" && ls -l /app && \
    echo "Listing /app/SSHVerbindung directory:" && ls -l /app/SSHVerbindung

CMD tail -f /dev/null
