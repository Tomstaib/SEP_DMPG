# Verwenden Sie ein Basis-Image von Miniconda mit Python 3.11
FROM continuumio/miniconda3:4.12.0

# Setze das Arbeitsverzeichnis
WORKDIR /usr/src/app

# Kopiere die environment.yml und requirements.txt Datei ins Arbeitsverzeichnis
COPY environment.yml .
COPY requirements.txt .

# Installiere Mamba
RUN conda install mamba -n base -c conda-forge && conda clean -afy && echo "Mamba installiert"

# Erstelle und aktiviere eine Python 3.11 Umgebung
RUN mamba create -n myenv python=3.11 && conda clean -afy && \
    echo "Python 3.11 Umgebung erstellt"

# Setze die Umgebungsvariable, damit die Umgebung "myenv" verwendet wird
ENV PATH /opt/conda/envs/myenv/bin:$PATH

# Aktualisiere die Umgebung mit environment.yml
RUN mamba env update --file environment.yml --name myenv && conda clean -afy && \
    echo "Umgebung aktualisiert mit environment.yml"

# Installiere pip-Abhängigkeiten aus requirements.txt in der conda Umgebung
RUN pip install --no-cache-dir -r requirements.txt || { \
    echo "Fehler bei der Installation von pip-Abhängigkeiten"; \
    exit 1; \
}

# Kopiere Ihre Anwendung
COPY . .

# Verifikation durchlaufen lassen
RUN echo "Conda list post-init" && conda list
RUN echo "Verifizierung Schritte" && conda info

# Setze den Eintragspunkt
CMD ["python", "CapacityCheck/CapacityCheck.py"]
