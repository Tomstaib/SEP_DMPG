# Basierend auf dem offiziellen Logstash Image
FROM docker.elastic.co/logstash/logstash:7.10.1

# Kopiere die Logstash-Konfigurationsdatei
COPY logstash.conf /usr/share/logstash/pipeline/logstash.conf

# Exponiere die Ports, die von Logstash verwendet werden
EXPOSE 5044 9600

# Start-Command für Logstash
CMD ["logstash", "-f", "/usr/share/logstash/pipeline/logstash.conf"]