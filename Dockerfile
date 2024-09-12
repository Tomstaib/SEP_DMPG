# Optimiertes Basis-Image von Miniconda verwenden.
FROM continuumio/miniconda3

# Setze das Arbeitsverzeichnis
WORKDIR /app

# Kopiere den gesamten Inhalt des aktuellen Verzeichnisses auf dem Host in das Arbeitsverzeichnis im Container
COPY . .

# Erstellen der Conda-Umgebung aus der environment.yml Datei
RUN conda env create -f environment.yml

# Aktivieren der Conda-Umgebung und diese als Standard festlegen
RUN echo "source activate myenv" > ~/.bashrc && \
    echo "conda activate myenv" >> ~/.bashrc
ENV PATH /opt/conda/envs/myenv/bin:$PATH

# Installiere notwendige System-Abhängigkeiten und Build-Tools
RUN apt-get update && apt-get install -y build-essential && apt-get clean

# Standardbefehl setzen, der ausgeführt wird, wenn der Container gestartet wird
# Hier wird einfach eine Bash-Shell gestartet, um den Container aktiv zu halten
CMD tail -f /dev/null