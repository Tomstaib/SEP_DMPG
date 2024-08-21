from flask import Flask
from flask_login import LoginManager
from models import User

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Flask-Login initialisieren
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


if __name__ == '__main__':
    from routes import *

    app.run(debug=True)
