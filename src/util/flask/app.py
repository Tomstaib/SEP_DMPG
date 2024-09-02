from functools import wraps
from flask import Flask, request, redirect, url_for, flash, render_template, session
from ssh_setup import setup_ssh_connection

app = Flask(__name__)
app.secret_key = 'your_secret_key'


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

            # Storing remote password for SSH in the session (ensure this is necessary and secure)
            session['remote_password'] = password

            # Attempt to set up SSH connection
            setup_ssh_connection(username)

            flash('Login successful and SSH key setup completed.')
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


if __name__ == "__main__":
    app.run(debug=True)
