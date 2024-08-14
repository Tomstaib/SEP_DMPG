import os
import psutil
import re
import cpuinfo

# Konstante für wiederverwendbare Literale
ACCEPTED = "Accepted"
NOT_ACCEPTED = "Not accepted"
NOT_ACCEPTED_CAPITALIZED = "Not Accepted"

##### CPU-Informationen abrufen #####

def get_cpu_info():
    """
    Abrufen der CPU-Informationen.

    Rückgabe:
        dict: Informationen über die Anzahl der physischen Kerne und die maximale CPU-Frequenz.
    """
    cpu_info = {
        "Anzahl der physischen Kerne": psutil.cpu_count(logical=False),
        "Maximale CPU-Frequenz": f"{psutil.cpu_freq().max / 1000:.2f} GHz"
    }
    return cpu_info


##### Speicherinformationen abrufen #####

def get_memory_info():
    """
    Abrufen der Speicherinformationen.

    Rückgabe:
        dict: Informationen über den Gesamtspeicher.
    """
    memory = psutil.virtual_memory()
    memory_info = {
        "Gesamtspeicher": f"{memory.total / (1024 ** 3):.2f} GB"
    }
    return memory_info


##### Modellnummer extrahieren #####

def get_model_number(brand_raw):
    """
    Extrahieren der Modellnummer aus einer gegebenen 'brand_raw'-Zeichenkette.

    Parameter:
        brand_raw (str): Die Rohmarkenbezeichnung des CPU.

    Rückgabe:
        int oder None: Die Modellnummer, falls gefunden, sonst None.
    """
    model_number = re.search(r"\d{3,5}", brand_raw)
    if model_number:
        return int(model_number.group())
    return None


##### Prozessortyp überprüfen #####

def check_processor_type():
    """
    Überprüfen des Prozessortyps, um festzustellen, ob er akzeptiert wird.

    Rückgabe:
        str: "Accepted" oder "Not accepted" je nach Prozessortyp und Modellnummer.
    """
    cpu_info = cpuinfo.get_cpu_info()
    INTEL_CORE_LEAST_GEN = 10000
    INTEL_XEON_LEAST_GEN = 2000
    AMD_LEAST_GEN = 5

    brand_raw = cpu_info["brand_raw"]
    model_number = get_model_number(brand_raw)

    if model_number is None:
        return "Not accepted (no model number found)"

    vendor = None
    if "Intel" in brand_raw:
        vendor = "Intel"
    elif "AMD" in brand_raw:
        vendor = "AMD"
    elif "Apple" in brand_raw:
        vendor = "Apple"

    if not vendor:
        return NOT_ACCEPTED

    match vendor:
        case "Intel" if "Xeon" in brand_raw:
            if model_number >= INTEL_XEON_LEAST_GEN:
                return ACCEPTED
            else:
                return NOT_ACCEPTED
        case "Intel" if "Core" in brand_raw:
            if model_number >= INTEL_CORE_LEAST_GEN:
                return ACCEPTED
            else:
                return NOT_ACCEPTED
        case "AMD":
            amd_model_number = re.search(r"\d{7}", brand_raw)
            if amd_model_number and int(amd_model_number.group()) >= AMD_LEAST_GEN:
                return ACCEPTED
            else:
                return NOT_ACCEPTED
        case "Apple":
            return ACCEPTED
        case _:
            return NOT_ACCEPTED


##### CPU-Kerne reservieren #####

def reserve_cores(percentage):
    """
    Reservieren eines Prozentsatzes der CPU-Kerne.

    Parameter:
        percentage (int): Der Prozentsatz der zu reservierenden CPU-Kerne.
    """
    num_physical_cores = psutil.cpu_count(logical=False)
    reserved_cores = int(num_physical_cores * percentage // 100)
    print(f"Anzahl der reservierten Kerne: {reserved_cores} von {num_physical_cores} ({percentage}%)")

    # Hier würde die tatsächliche Reservierung der Kerne erfolgen, falls notwendig.
    # Beispiel: CPU-Affinität setzen (bind to cores)
    p = psutil.Process(os.getpid())
    core_ids = list(range(reserved_cores))
    p.cpu_affinity(core_ids)


##### Arbeitsspeicher reservieren #####

def reserve_memory(percentage):
    """
    Reservieren eines Prozentsatzes des gesamten Arbeitsspeichers.

    Parameter:
        percentage (int): Der Prozentsatz des zu reservierenden Arbeitsspeichers.

    Rückgabe:
        bytearray: Das reservierte Speichersegment.
    """
    total_memory = psutil.virtual_memory().total
    reserved_memory = int(total_memory * percentage / 100)
    dummy_data = bytearray(reserved_memory)
    print(f"Reservierter Speicher: {reserved_memory / (1024 ** 3):.2f} GB von {total_memory / (1024 ** 3):.2f} GB ({percentage}%)")
    return dummy_data


##### Hardwareanforderungen überprüfen #####

def check_hardware_requirements():
    """
    Überprüfen der Hardware-Anforderungen und Reservieren von Ressourcen, falls diese erfüllt sind.
    """
    # Mindestanforderungen
    cpu_type = cpuinfo.get_cpu_info()
    MIN_PHYSICAL_CORES = 4
    MIN_MAX_CPU_FREQ = 4.0
    MIN_MEMORY_GB = 8

    # CPU-Informationen
    cpu_info = get_cpu_info()
    num_physical_cores = int(cpu_info["Anzahl der physischen Kerne"])
    max_cpu_freq = float(psutil.cpu_freq().max / 1000)

    # Überprüfen, ob die CPU die Mindestanforderungen erfüllt
    cpu_core_result = "Accepted" if (num_physical_cores >= MIN_PHYSICAL_CORES) else NOT_ACCEPTED_CAPITALIZED

    # Überprüfen, ob die MIN_MAX_CPU_FREQ erfüllt wird
    cpu_freq_result = "Accepted" if (max_cpu_freq >= MIN_MAX_CPU_FREQ) else NOT_ACCEPTED_CAPITALIZED

    # Speicherinformationen
    memory_info = get_memory_info()
    total_memory_gb = float(memory_info["Gesamtspeicher"].split()[0])

    # Überprüfen, ob der Speicher die Mindestanforderung erfüllt
    memory_result = "Accepted" if total_memory_gb >= MIN_MEMORY_GB else NOT_ACCEPTED_CAPITALIZED

    # Ergebnis der Hardware-Anforderungen
    hardware_accepted = (cpu_freq_result == "Accepted" and cpu_core_result == "Accepted" and memory_result == "Accepted" and check_processor_type() == "Accepted")

    # Ausgabe in tabellarischer Form
    print("\nHardware-Anforderungen:")
    print(f"{'-' * 40}")
    print(f"{'CPU-Modell:':<20} {cpu_type['brand_raw']:<20} {check_processor_type():>20}")
    print(f"{'Maximale CPU-Frequenz:':<20} {max_cpu_freq:.2f} GHz{'':<20} {cpu_freq_result:>20}")
    print(f"{'Anzahl der physischen Kerne:':<20} {num_physical_cores:<20} {cpu_core_result:>20}")
    print(f"{'Arbeitsspeicher:':<20} {total_memory_gb:.2f} GB{'':<20} {memory_result:>20}")
    print(f"{'-' * 40}")

    # Reservieren von CPU-Kernen und Arbeitsspeicher nur, wenn alle Anforderungen erfüllt werden
    if hardware_accepted:
        reserve_cores(90)
        _ = reserve_memory(30)  # 30% des Arbeitsspeichers reservieren
        try:
            print(f"Aktuelle PID: {os.getpid()}")
            # Endlosschleife, um das Skript aktiv zu halten
            while True:
                # TODO: Funktion muss vollständig implementiert werden.
                pass
        except KeyboardInterrupt:
            print("\nScript wurde beendet.")
    else:
        print("Mindestanforderungen nicht erfüllt. CPU-Kerne und Arbeitsspeicher werden nicht reserviert.")
        print(f"Aktuelle PID: {os.getpid()}")

##### Aufruf der Funktion, um Hardware-Anforderungen zu überprüfen #####

check_hardware_requirements()