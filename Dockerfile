FROM continuumio/miniconda3

# Kopieren Sie Ihre environment.yml
COPY environment.yml /tmp/environment.yml

# Update die Umgebungen mithilfe von Mamba/Conda
RUN conda install mamba -n base -c conda-forge && \
    mamba env update --file /tmp/environment.yml --name base && \
    conda clean -afy

# Stellen Sie sicher, dass keine fehlerhaften Dateien vorhanden sind
RUN echo "Conda list pre-init" \
    && conda list

# Kopieren Sie Ihr Projekt
WORKDIR /usr/src/app
COPY . .

# Installationsschritte zum Debuggen hinzufügen
RUN echo "Verifizierung Schritte" && conda info 

# Stellen Sie sicher, dass der Eintragspunkt
CMD ["python", "CapacityCheck.py"]
