import os
import secrets
from datetime import datetime
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, current_app
from flask_login import login_user, current_user, logout_user, login_required
from uhs12app import db, bcrypt, mail
from uhs12app.users.forms import (
    RegistrationForm,
    LoginForm,
    RequestResetForm,
    ResetPasswordForm,
)
from uhs12app.models import User, House, Invite, Task, TaskLog, ShamePost
from flask_mail import Message
from flask import Blueprint

users = Blueprint('users', __name__)


@users.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    primary_house = current_user.active_house()
    # List of joined houses that are not my currently active house
    other_joined = [member.house for member in current_user.active_memberships() if member.houseId != primary_house.id]
    return render_template("profile.html", current_user=current_user, house=primary_house, other_joined=other_joined)


@users.route("/setactive", methods=["GET", "POST"])
@login_required
def setactive():
    """Set which house is your active house"""
    house_id = request.args.get("houseid")
    current_user.activeHouseId = house_id
    db.session.commit()
    return redirect(url_for("users.profile"))


@users.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("tasks.home"))
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter(User.email.ilike(login_form.email.data)).first()
        if user and bcrypt.check_password_hash(user.password, login_form.password.data):
            login_user(user, remember=login_form.remember.data)
            if user.activeHouseId:
                return redirect(url_for("tasks.home"))
            return redirect(url_for("house.whathouse"))
            # next_page = request.args.get("next")
            # return redirect(next_page) if next_page else redirect(url_for("tasks.home"))
        else:
            flash("Bad login! Check your email and password", "danger")
    return render_template("login.html", form=login_form)


@users.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("tasks.home"))
    regForm = RegistrationForm()
    if regForm.validate_on_submit():
        hashedPw = bcrypt.generate_password_hash(regForm.password.data).decode("utf-8")
        user = User(
            username=regForm.username.data, email=regForm.email.data, password=hashedPw
        )
        db.session.add(user)
        db.session.commit()
        flash(
            f"Account created for {regForm.username.data}! You can now log in",
            "success",
        )
        return redirect(url_for("users.login"))
    return render_template("signup.html", form=regForm)


@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("tasks.home"))


def send_reset_email(user):
    token = user.get_reset_token()
    # msg = Message('Password Reset Request', sender='noreply@demo.com', recipients=[user.email])
    msg = Message('Password Reset Request', sender=current_app.config['MAIL_USERNAME'], recipients=[user.email])
    msg.body = f"""
    To reset your password, visit the following link: 
    {url_for('users.reset_token', token=token, _external=True)}
    
    If you did not request a password reset then please ignore this email. 
    """
    mail.send(msg)

@users.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    """

    """
    if current_user.is_authenticated:
        return redirect(url_for("tasks.home"))
    resetForm = RequestResetForm()
    if resetForm.validate_on_submit():
        user = User.query.filter_by(email=resetForm.email.data).first()
        send_reset_email(user)
        print(f"Emailing: {user.email}")
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('users.login'))
    return render_template("reset_request.html", title='Reset Password', form=resetForm)

@users.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    """

    """
    if current_user.is_authenticated:
        return redirect(url_for("tasks.home"))
    user = User.verify_reset_token(token)
    if not user:
        flash('Thas is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))
    pwForm = ResetPasswordForm()
    if pwForm.validate_on_submit():
        hashedPw = bcrypt.generate_password_hash(pwForm.password.data).decode("utf-8")
        user.password = hashedPw
        db.session.commit()
        flash(
            f"Your password has been updated! You can now log in", "success",
        )
        return redirect(url_for("users.login"))
    return render_template("reset_token.html", title='Reset Password', form=pwForm)
