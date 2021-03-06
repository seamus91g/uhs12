from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from uhs12app.config import Config


db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "users.login"
login_manager.login_message_category = "info"

mail = Mail()
def create_app(config_class=Config, create_db=False):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from uhs12app.users.routes import users
    from uhs12app.tasks.routes import tasks
    from uhs12app.house.routes import house
    from uhs12app.main.routes import main
    from uhs12app.errors.handlers import errors
    app.register_blueprint(users)
    app.register_blueprint(tasks)
    app.register_blueprint(house)
    app.register_blueprint(main)
    app.register_blueprint(errors)


    if create_db:
        print("Creating db at: ", config_class.SQLALCHEMY_DATABASE_URI)
        with app.app_context():
            db.create_all()

    return app
