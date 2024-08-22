# Basis-Image mit Miniconda von conda-forge
FROM continuumio/miniconda3:4.12.0

# Arbeitsverzeichnis setzen
WORKDIR /usr/src/app

# Installiere die notwendigen System-Bibliotheken
RUN apt-get update && apt-get install -y libarchive13 && rm -rf /var/lib/apt/lists/*

# Installiere Mamba
RUN conda install mamba -n base -c conda-forge && conda clean -afy && echo "Mamba installiert"

# Erstelle und aktiviere eine Python 3.11 Umgebung
RUN mamba create -n myenv python=3.11 && conda clean -afy && echo "Python 3.11 Umgebung erstellt"

# Setze die Umgebungsvariable, damit die Umgebung "myenv" verwendet wird
ENV PATH /opt/conda/envs/myenv/bin:$PATH

# Anforderungen kopieren und installieren
COPY environment.yml .
COPY requirements.txt .

# Entferne unsichtbare Zeichen aus requirements.txt und speichere in einer neuen Datei
RUN sed 's/[^[:print:]\t]//g' requirements.txt > clean_requirements.txt && \
    echo "Inhalt von cleanrequirements.txt: " && cat cleanrequirements.txt

# Installiere pip-Abhängigkeiten aus der bereinigten requirements.txt in der conda Umgebung
RUN pip install --no-cache-dir -r clean_requirements.txt || { \
    echo "Fehler bei der Installation von pip-Abhängigkeiten"; \
    exit 1; \
}
    
# Anwendungscode kopieren
COPY . .

# Verifikation 
RUN echo "Conda list post-init" && conda list
RUN echo "Verifizierung Schritte" && conda info

# Startbefehl setzen (falls erforderlich)
CMD ["python", "CapacityCheck/CapacityCheck.py"]
