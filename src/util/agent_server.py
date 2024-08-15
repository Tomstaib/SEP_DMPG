from flask import Flask, request, jsonify, send_file, render_template_string
import subprocess
import os
import uuid
import shutil

app = Flask(__name__)

# Verzeichnis für generierte Agenten und Arbeitsverzeichnis
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.join(BASE_DIR, "agents")

if not os.path.exists(AGENTS_DIR):
    os.makedirs(AGENTS_DIR)

# In-Memory-Datenstruktur zur Speicherung der gültigen API-Schlüssel
valid_api_keys = {}

# HTML-Template für die Startseite
HTML_TEMPLATE = '''
<!doctype html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Generate Agent</title>
    <style>
        #loading {
            display: none;
            width: 100%;
            text-align: center;
            margin-top: 20px;
        }
        #loading img {
            width: 50px;
            height: 50px;
        }
    </style>
</head>
<body>
    <h1>Generate Agent</h1>
    <form id="agentForm" action="/generate_agent" method="post" onsubmit="showLoading()">
        <button type="submit">Generate Agent</button>
    </form>
    <div id="loading">
        <img src="https://i.imgur.com/llF5iyg.gif" alt="Loading..."/>
        <p>Generating your agent, please wait...</p>
    </div>
    {% if download_link %}
        <p>Download your agent: <a href="{{ download_link }}">{{ download_link }}</a></p>
    {% endif %}

    <script>
        function showLoading() {
            document.getElementById('agentForm').style.display = 'none';
            document.getElementById('loading').style.display = 'block';
        }
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/generate_agent', methods=['POST'])
def generate_agent():
    # Generate a unique API key
    api_key = str(uuid.uuid4())
    valid_api_keys[api_key] = True  # Mark the API key as valid

    # Create the agent script with the unique API key
    agent_script = f"""
import socket
import requests

def get_system_info():
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    return hostname, ip_address

def send_data_to_server(server_url, data, api_key):
    headers = {{
        'Authorization': f'Bearer {{api_key}}',
        'Content-Type': 'application/json'
    }}
    try:
        response = requests.post(server_url, json=data, headers=headers)
        response.raise_for_status()
        print("Data successfully sent.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending data: {{e}}")

if __name__ == "__main__":
    server_url = "http://192.168.188.40:5000/receive_data"
    api_key = "{api_key}"

    hostname, ip_address = get_system_info()
    data = {{
        "hostname": hostname,
        "ip_address": ip_address
    }}

    send_data_to_server(server_url, data, api_key)
    """

    # Ensure the agents directory exists
    if not os.path.exists(AGENTS_DIR):
        try:
            print(f"Creating agents directory at: {AGENTS_DIR}")
            os.makedirs(AGENTS_DIR)
        except Exception as e:
            print(f"Failed to create agents directory: {e}")
            return "Error: Failed to create agents directory", 500

    # Save the agent script to a file
    agent_filename = os.path.join(AGENTS_DIR, f"agent_{api_key}.py")
    print(f"Creating agent script at: {agent_filename}")
    try:
        with open(agent_filename, 'w') as f:
            f.write(agent_script)
        print(f"Successfully created the agent script at: {agent_filename}")
    except Exception as e:
        print(f"Failed to create the agent script at: {agent_filename}, error: {e}")
        return f"Error: Failed to create the agent script, error: {e}", 500

    # Check if the file was created
    if not os.path.exists(agent_filename):
        print(f"Failed to create the agent script at: {agent_filename}")
        return "Error: Failed to create the agent script", 500

    # Change to the working directory
    original_cwd = os.getcwd()
    os.chdir(BASE_DIR)

    # Create an executable from the script
    try:
        subprocess.run(['pyinstaller', '--onefile', agent_filename], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to create executable: {e}")
        return f"Error: Failed to create executable, error: {e}", 500

    # Path to the executable
    exe_filename = os.path.join(BASE_DIR, "dist", f"agent_{api_key}.exe")
    spec_filename = os.path.join(BASE_DIR, f"agent_{api_key}.spec")

    # Debug output to ensure the file exists
    if os.path.exists(exe_filename):
        print(f"Created executable file: {exe_filename}")
    else:
        print(f"Error: File {exe_filename} not found!")

    # Clean up the temporary script and build directories (except `dist`)
    try:
        os.remove(agent_filename)
        if os.path.exists(spec_filename):
            os.remove(spec_filename)  # Remove the .spec file if it exists
        if os.path.exists(os.path.join(BASE_DIR, 'build')):
            shutil.rmtree(os.path.join(BASE_DIR, 'build'))
        if os.path.exists(os.path.join(BASE_DIR, '__pycache__')):
            shutil.rmtree(os.path.join(BASE_DIR, '__pycache__'))
    except Exception as e:
        print(f"Cleanup error: {e}")

    # Change back to the original working directory
    os.chdir(original_cwd)

    # Offer the executable file for download
    return render_template_string(HTML_TEMPLATE, download_link=f'/download/{api_key}')


@app.route('/download/<api_key>')
def download_agent(api_key):
    exe_filename = os.path.join(BASE_DIR, "dist", f"agent_{api_key}.exe")
    if os.path.exists(exe_filename):
        return send_file(exe_filename, as_attachment=True)
    else:
        return f"Fehler: Datei {exe_filename} wurde nicht gefunden!", 404


"""@app.route('/receive_data', methods=['POST'])
def receive_data():
    try:
        data = request.get_json()
        api_key = request.headers.get('Authorization').split(" ")[1]

        if api_key not in valid_api_keys:
            return jsonify({"message": "Invalid API key"}), 403

        hostname = data.get('hostname')
        ip_address = data.get('ip_address')
        if not hostname or not ip_address:
            return jsonify({"message": "Hostname or IP address missing"}), 400

        print(f"Received hostname: {hostname}, IP address: {ip_address}")

        # API-Schlüssel nach Verwendung ungültig machen
        del valid_api_keys[api_key]

        return jsonify({"message": "Data received successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500"""


@app.route('/receive_data', methods=['POST'])
def receive_data():
    try:
        data = request.get_json()
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"message": "Missing Authorization header"}), 401

        api_key = auth_header.split(" ")[1]

        if api_key not in valid_api_keys:
            return jsonify({"message": "Invalid API key"}), 403

        hostname = data.get('hostname')
        ip_address = data.get('ip_address')
        if not hostname or not ip_address:
            return jsonify({"message": "Hostname or IP address missing"}), 400

        print(f"Received hostname: {hostname}, IP address: {ip_address}")

        # API-Schlüssel nach Verwendung ungültig machen
        del valid_api_keys[api_key]

        return jsonify({"message": "Data received successfully"}), 200
    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
