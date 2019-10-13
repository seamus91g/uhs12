from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from uhs12app.models import User, House

# from flask_wtf.file import FileField, FileAllowed
# from flask_login import current_user


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        # TODO: customise this per house, instead of across the entire database. This could 
        # be awkward because username is decided before they actually join a house. Maybe decide username at that point
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('An account already exists for this email!')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class NewHouseForm(FlaskForm):
    name = StringField('House name',
                           validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField('Create House')

    def validate_name(self, name):
        house = House.query.filter_by(name=name.data).first()
        if house:
            raise ValidationError('That house name is taken. Please choose a different one.')

class JoinHouseForm(FlaskForm):
    name = StringField('House name',
                           validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField('Join House')

    def validate_name(self, name):
        house = House.query.filter_by(name=name.data).first()
        if not house:
            raise ValidationError('That house does not exist!')


class ReplyInviteForm(FlaskForm):
    
    submitAccept = SubmitField('accept')
    submitDecline = SubmitField('decline')
