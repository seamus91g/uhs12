import os

class Config(object):

    SECRET_KEY = os.environ.get("UHS_SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("UHS_SQLALCHEMY_DATABASE_URI")
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    # $env:EMAIL_UHS12CONTACT = ""
    MAIL_USERNAME = os.environ.get('EMAIL_UHS12CONTACT')
    MAIL_PASSWORD = os.environ.get('UHS12CONTACT_PASS')

