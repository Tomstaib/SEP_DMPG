# Verwenden Sie ein Basis-Image von Miniconda
FROM continuumio/miniconda3

# Setze das Arbeitsverzeichnis
WORKDIR /usr/src/app

# Kopiere die environment.yml Datei ins Arbeitsverzeichnis
COPY environment.yml .
COPY requirements.txt .

# Installiere Mamba und aktualisiere die Umgebung
RUN conda install mamba -n base -c conda-forge && \
    mamba env update --file environment.yml --name base && \
    mamba install --name base pip && \
    pip install --no-cache-dir -r requirements.txt && \
    conda clean -afy

# Kopiere den Rest des Codes
COPY . .

# Verifikation durchlaufen lassen
RUN echo "Conda list post-init" \
    && conda list

RUN echo "Verifizierung Schritte" && conda info 

# Setze den Eintragspunkt
CMD ["python", "CapacityCheck/CapacityCheck.py"]
