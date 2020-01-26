import os
import json 


class Config(object):

    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    if os.name == 'nt':
        # $env:EMAIL_UHS12CONTACT = ""
        MAIL_USERNAME = os.environ.get('EMAIL_UHS12CONTACT')
        MAIL_PASSWORD = os.environ.get('UHS12CONTACT_PASS')
        SECRET_KEY = os.environ.get("UHS_SECRET_KEY")
        SQLALCHEMY_DATABASE_URI = os.environ.get("UHS_SQLALCHEMY_DATABASE_URI")
    else:
        with open('/etc/uhsconfig.json') as config_file:
            config = json.load(config_file)
        SQLALCHEMY_DATABASE_URI = config.get("UHS_SQLALCHEMY_DATABASE_URI")
        SECRET_KEY = config.get("UHS_SECRET_KEY")
        MAIL_USERNAME = config.get('EMAIL_UHS12CONTACT')
        MAIL_PASSWORD = config.get('UHS12CONTACT_PASS')

