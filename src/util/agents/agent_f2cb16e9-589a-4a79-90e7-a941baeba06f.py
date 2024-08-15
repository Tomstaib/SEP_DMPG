
import socket
import requests

def get_system_info():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return hostname, ip_address

def send_data_to_server(server_url, data, api_key):
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(server_url, json=data, headers=headers)
        response.raise_for_status()
        print("Daten erfolgreich gesendet.")
    except requests.exceptions.RequestException as e:
        print(f"Fehler beim Senden der Daten: {e}")

if __name__ == "__main__":
    server_url = "http://192.168.188.40:5000/receive_data"
    api_key = "f2cb16e9-589a-4a79-90e7-a941baeba06f"
    
    hostname, ip_address = get_system_info()
    data = {
        "hostname": hostname,
        "ip_address": ip_address
    }
    
    send_data_to_server(server_url, data, api_key)
    