import os
import secrets
from datetime import datetime
from PIL import Image
from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from uhs12app import app, db, bcrypt, mail
from uhs12app.forms import (
    RegistrationForm,
    LoginForm,
    NewHouseForm,
    JoinHouseForm,
    ReplyInviteForm,
    NewTaskForm,
    NewShamePostForm,
    RequestResetForm,
    ResetPasswordForm,
)
from uhs12app.models import User, House, Invite, Task, TaskLog, ShamePost
from flask_mail import Message


@app.route("/")
@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    """
    The home page will contain your list of tasks
    """
    if not current_user.houseId:
        return redirect(url_for("whathouse"))
    allTasks = Task.query.filter_by(houseId=current_user.houseId)
    return render_template("home.html", tasks=allTasks)


@app.route("/taskcomplete", methods=["GET", "POST"])
@login_required
def taskcomplete():
    taskCompleted = Task.query.filter_by(id=int(request.args["taskid"])).first()
    # TODO if last completed date is with cool off window, value is cool off value
    taskItem = TaskLog(
        houseId=current_user.houseId,
        taskId=taskCompleted.id,
        idUser=current_user.id,
        value=taskCompleted.currentValue(),
        coolOff=taskCompleted.isCooloffActive(),
    )
    taskCompleted.updateCompleted(current_user)
    db.session.add(taskItem)
    db.session.commit()
    flash(f"Great work! You completed task '{taskCompleted.name}'", "success")
    return redirect(url_for("home"))


@app.route("/tasklog")
@login_required
def tasklog():
    page_num = request.args.get('page', 1, type=int)
    allTasksCompleted = TaskLog.query.order_by(TaskLog.dateCreated.desc()).filter_by(houseId=current_user.houseId).paginate(per_page=20, page=page_num)
    return render_template(
        "tasklog.html", tasklog=allTasksCompleted, currUser=current_user
    )


@app.route("/taskdelete", methods=["GET", "POST"])
@login_required
def taskdelete():
    taskLogItem = TaskLog.query.filter_by(id=int(request.args["taskid"])).first()
    nameDeleted = taskLogItem.task.name
    db.session.delete(taskLogItem)
    db.session.commit()
    flash(f"You deleted task '{nameDeleted}'", "info")
    return redirect(url_for("home"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, login_form.password.data):
            login_user(user, remember=login_form.remember.data)
            if user.houseId:
                return redirect(url_for("home"))
            return redirect(url_for("whathouse"))
            # next_page = request.args.get("next")
            # return redirect(next_page) if next_page else redirect(url_for("home"))
        else:
            flash("Bad login! Check your email and password", "danger")
    return render_template("login.html", form=login_form)


def save_picture(form_picture, sub_dir="wos_pics", output_size=(512, 512)):
    """
    Save a picture to the file system. 
    Assign random name in case users upload two pics with same name. 
    Picture will be resized to specified dimensions before being saved. 
    """
    # Keep the extension but randomise the name
    rand_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = rand_hex + f_ext
    # Save the desired sub directory in the static folder
    pic_path = os.path.join(app.root_path, 'static', sub_dir, picture_fn)
    # Scale the image according to parameters given by output_size
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(pic_path)
    # Return the new name for the picture
    return picture_fn


@app.route("/wallofshame", methods=["GET", "POST"])
def wallofshame():
    # TODO Tally disapprovals and apply them when user leaves the page
    shame_form = NewShamePostForm()
    if shame_form.validate_on_submit():
        pic_name = save_picture(shame_form.picture.data, sub_dir="wos_pics", output_size=(1024, 1024))
        shame_post = ShamePost(
            houseId=current_user.houseId,
            userId=current_user.id,
            postImage=pic_name,
        )
        db.session.add(shame_post)
        db.session.commit()
        flash(f"Hooray! You have cast shame!", "success")
        return redirect(url_for("wallofshame"))
    
    shame_posts = ShamePost.query.filter_by(houseId=current_user.houseId).all()

    return render_template("wallofshame.html", shame_posts=shame_posts, form=shame_form)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
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
        return redirect(url_for("login"))
    return render_template("signup.html", form=regForm)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/myhouse", methods=["GET", "POST"])
@login_required
def myhouse():
    """
    This lists the members of the house and the points that they each have 
    """
    if not current_user.houseId:
        return redirect(url_for("whathouse"))
    house = House.query.filter_by(id=current_user.houseId).first()
    # TODO only allow the admin user to see the invites
    invitesWaiting = {}
    for invite in Invite.query.filter_by(
        houseId=current_user.houseId, isResponded=False
    ).all():
        user = User.query.filter_by(id=invite.idUserInvited).first()
        # TODO understand why prefix is necessary, without it both forms are submitted together
        invitesWaiting[user] = ReplyInviteForm(prefix="{}".format(user.username))
    for invUser, invForm in invitesWaiting.items():
        if invForm.validate_on_submit():
            invite = Invite.query.filter_by(
                houseId=current_user.houseId,
                idUserInvited=invUser.id,
                isResponded=False,
            ).first()
            invite.isResponded = True
            if invForm.submitAccept.data:
                invUser.houseId = current_user.houseId
            if invForm.submitDecline.data:
                # TODO send the user a message about the invite being declined?
                pass
            db.session.commit()
            return redirect(url_for("myhouse"))
    # TODO make this an OrderedDict and sort by person with most points
    pts_users = TaskLog.pointsAllUsers(db.session, current_user.houseId)
    return render_template("myhouse.html", house=house.name, invites=invitesWaiting, points=pts_users)


@app.route("/whathouse")
@login_required
def whathouse():
    """
    Choose to either create a house or join an existing one 
    """
    if current_user.houseId:
        return redirect(url_for("home"))
    open_invite = checkWaitingOnInvite(current_user)
    house_name = None
    if open_invite:
        house_name = House.query.filter_by(id=open_invite.houseId).first().name
    return render_template("whathouse.html", pending_invite=house_name)


# TODO make this a decorator
def checkWaitingOnInvite(userWaiting):
    # TODO if filter by isResponded then can drop the loop
    for sent_invite in Invite.query.filter_by(idUserInvited=userWaiting.id).all():
        if not sent_invite.isResponded:
            return sent_invite


@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """
    Form for creating a house 
    """
    if current_user.houseId:
        return redirect(url_for("home"))
    if checkWaitingOnInvite(current_user):
        return redirect(url_for("whathouse"))
    houseForm = NewHouseForm()
    if houseForm.validate_on_submit():
        newHouse = House(name=houseForm.name.data, adminId=current_user.id)
        db.session.add(newHouse)
        db.session.commit()
        # newHouse only gets an id after commit, thus we need two commits
        current_user.houseId = newHouse.id
        db.session.commit()
        flash(f"House {houseForm.name.data} created!", "success")
        return redirect(url_for("home"))
    return render_template("create.html", form=houseForm)


@app.route("/join", methods=["GET", "POST"])
@login_required
def join():
    """
    Join a house by name
    """
    if current_user.houseId:
        return redirect(url_for("home"))
    # If the user has an ongoing invite, don't let them send another one
    if checkWaitingOnInvite(current_user):
        flash(
            "Already waiting to join a house. Wait for response before trying to join another",
            "info",
        )
        return redirect(url_for("whathouse"))
    join_form = JoinHouseForm()
    if join_form.validate_on_submit():
        house = House.query.filter_by(name=join_form.name.data).first()
        new_invite = Invite(houseId=house.id, idUserInvited=current_user.id)
        db.session.add(new_invite)
        db.session.commit()
        flash(f"Requested to join {join_form.name.data}!", "success")
        return redirect(url_for("whathouse"))
    return render_template("join.html", form=join_form)


@app.route("/newtask", methods=["GET", "POST"])
@login_required
def newtask():
    if not current_user.houseId:
        return redirect(url_for("whathouse"))
    taskForm = NewTaskForm()
    if taskForm.validate_on_submit():
        task = Task(
            houseId=current_user.houseId,
            name=taskForm.name.data,
            description=taskForm.description.data,
            value=taskForm.value.data,
            coolOffPeriod=taskForm.coolOffPeriod.data,
            coolOffValue=taskForm.coolOffValue.data,
        )
        db.session.add(task)
        db.session.commit()
        flash(f"Task '{taskForm.name.data}' created!", "success")
        return redirect(url_for("home"))

    return render_template("newtask.html", form=taskForm)

def send_reset_email(user):
    token = user.get_reset_token()
    # msg = Message('Password Reset Request', sender='noreply@demo.com', recipients=[user.email])
    msg = Message('Password Reset Request', sender=app.config['MAIL_USERNAME'], recipients=[user.email])
    msg.body = f"""
    To reset your password, visit the following link: 
    {url_for('reset_token', token=token, _external=True)}
    
    If you did not request a password reset then please ignore this email. 
    """
    mail.send(msg)

@app.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    """

    """
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    resetForm = RequestResetForm()
    if resetForm.validate_on_submit():
        user = User.query.filter_by(email=resetForm.email.data).first()
        send_reset_email(user)
        print(f"Emailing: {user.email}")
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template("reset_request.html", title='Reset Password', form=resetForm)

@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    """

    """
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    user = User.verify_reset_token(token)
    if not user:
        flash('Thas is an invalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    pwForm = ResetPasswordForm()
    if pwForm.validate_on_submit():
        hashedPw = bcrypt.generate_password_hash(pwForm.password.data).decode("utf-8")
        user.password = hashedPw
        db.session.commit()
        flash(
            f"Your password has been updated! You can now log in", "success",
        )
        return redirect(url_for("login"))
    return render_template("reset_token.html", title='Reset Password', form=pwForm)
