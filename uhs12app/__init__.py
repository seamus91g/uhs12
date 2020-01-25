import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail


app = Flask(__name__)
app.config["SECRET_KEY"] = "6dfbd4331efcd5ca9d8548cfb84a8c70"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "users.login"
login_manager.login_message_category = "info"
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
# $env:EMAIL_UHS12CONTACT = ""
app.config['MAIL_USERNAME'] = os.environ.get('EMAIL_UHS12CONTACT')
app.config['MAIL_PASSWORD'] = os.environ.get('UHS12CONTACT_PASS')
mail = Mail(app)

from uhs12app.users.routes import users
from uhs12app.tasks.routes import tasks
from uhs12app.house.routes import house
from uhs12app.main.routes import main

app.register_blueprint(users)
app.register_blueprint(tasks)
app.register_blueprint(house)
app.register_blueprint(main)

