import os
from functools import wraps
from flask import Flask, request, redirect, url_for, flash, render_template, session
from paramiko.client import SSHClient

from ssh_setup import setup_ssh_connection, close_ssh_connection
from util.flask.ssh_with_parameters import prepare_env

app = Flask(__name__)
app.secret_key = 'your_secret_key'
USER_DIR = r'/var/www/dmpg_api/user'


@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    else:
        return redirect(url_for('login'))


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('You need to log in first.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            # Basic validation (ensure username and password are provided)
            if not username or not password:
                flash('Username and password are required.')
                return render_template('login.html')

            # Storing username in the session
            session['username'] = username

            # Storing remote password for SSH in the session
            session['remote_password'] = password

            # Attempt to set up SSH connection
            ssh_client: SSHClient = setup_ssh_connection(username)

            flash('Login successful and SSH key setup completed.')
            user_folder = os.path.join(USER_DIR, username)
            try:
                if not os.path.exists(user_folder):
                    os.makedirs(user_folder)
                    flash(f"Folder for user '{username}' has been created.")
                else:
                    flash(f"Folder for user '{username}' already exists.")
            except OSError as e:
                flash(f"An error occurred while creating the folder: {e}")
                print(f"Error creating directory: {e}")
                with open("log.txt", "a") as f:
                    f.write(f"{e}")
                    f.close()
            ssh_client.close()
            return redirect(url_for('dashboard'))
    except Exception as e:
        # Log the error (optional: integrate with logging framework)
        print(f"An error occurred: {e}")

        # Flash a message to the user
        flash('An error occurred during the login process. Please try again.')

        # Optionally, redirect back to login or render the login page again with the error message
        return render_template('login.html')

    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))


@app.route('/settings')
@login_required  # Ensure the user is logged in to access this page
def settings():
    return render_template('settings.html')


@app.route('/new_job')
@login_required
def new_job():
    return render_template('new_job.html')


@app.route('/prepare-env', methods=['POST'])
@login_required
def prepare_env_route():
    try:
        prepare_env()  # Call the function
        flash("Environment preparation started successfully.")
    except Exception as e:
        print(f"Error: {e}")
        flash(f"An error occurred: {e}")

    # Redirect back to the new_job page after processing
    return redirect(url_for('new_job'))

if __name__ == "__main__":
    app.run(debug=True)
