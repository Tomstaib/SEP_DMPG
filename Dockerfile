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
ENV PATH=/opt/conda/envs/my_env/bin:$PATH

# Füge das Arbeitsverzeichnis zum PYTHONPATH hinzu
ENV PYTHONPATH=/app
# Hier wird einfach eine Bash-Shell gestartet, um den Container aktiv zu halten
CMD tail -f /dev/null
