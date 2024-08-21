from flask import render_template, redirect, url_for, request, flash, send_file
from flask_login import login_user, login_required, logout_user, current_user
import os
from app import app
from models import User
from ssh_auth import ssh_login
import logging
from flask import session
logging.basicConfig(level=logging.DEBUG)
import paramiko

def ssh_login_with_key(host, username, key_path):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=username, key_filename=key_path)
        return client
    except Exception as e:
        print(f'SSH login failed: {e}')
        return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        host = "hpc.hs-osnabrueck.de"
        key_path = r"C:\Users\Felix\Documents\GitHub\SEP_DMPG\src\util\flask\keys"  # Pfad zum privaten Schlüssel

        ssh_client = ssh_login_with_key(host, username, key_path)
        if ssh_client:
            user = User(username)
            login_user(user)
            session['ssh_host'] = host
            session['ssh_username'] = username
            session['ssh_key_path'] = key_path  # Speichern des Pfads zum Schlüssel
            flash('Login successful.')
            return redirect(url_for('select_results'))
        else:
            flash('Login failed. SSH authentication unsuccessful.')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/home')
@login_required
def home():
    return render_template('home.html', name=current_user.id)


@app.route('/logout')
@login_required
def logout():
    current_user.close_ssh_connection()
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))


@app.route('/select_results')
@login_required
def select_results():
    try:
        host = session.get('ssh_host')
        username = session.get('ssh_username')
        key_path = session.get('ssh_key_path')

        if not host or not username or not key_path:
            flash('Missing SSH connection information.')
            return redirect(url_for('login'))

        ssh_client = ssh_login_with_key(host, username, key_path)
        if ssh_client is None:
            flash('Failed to re-establish SSH connection.')
            return redirect(url_for('login'))

        sftp = ssh_client.open_sftp()
        remote_path = '/home/fegladen/src/SEP'
        files_on_server = sftp.listdir(remote_path)
        sftp.close()
        ssh_client.close()  # Schließen Sie die Verbindung nach Gebrauch

        local_path = os.path.join('/local/simulation/results', current_user.id)
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        downloaded_files = os.listdir(local_path)

        return render_template('select_results.html', files_on_server=files_on_server,
                               downloaded_files=downloaded_files)
    except Exception as e:
        flash(f'Failed to retrieve file list: {e}')
        return redirect(url_for('home'))
