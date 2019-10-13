
from datetime import datetime
from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from uhs12app import app, db, bcrypt
from uhs12app.forms import RegistrationForm, LoginForm, NewHouseForm, JoinHouseForm, ReplyInviteForm, NewTaskForm
from uhs12app.models import User, House, Invite, Task, TaskLog


@app.route("/")
@app.route("/home")
@login_required
def home():
    '''
    The home page will contain your list of tasks
    '''
    if not current_user.houseId:
        return redirect(url_for("whathouse"))
    allTasks = Task.query.all()
    return render_template('home.html', tasks=allTasks)


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
    return render_template('login.html', form=login_form)


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    regForm = RegistrationForm()
    if regForm.validate_on_submit():
        hashedPw = bcrypt.generate_password_hash(regForm.password.data).decode("utf-8")
        user = User(username=regForm.username.data, email=regForm.email.data, password=hashedPw)
        db.session.add(user)
        db.session.commit()
        flash(f"Account created for {regForm.username.data}! You can now log in", "success")
        return redirect(url_for("login"))
    return render_template('signup.html', form=regForm)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/myhouse")
@app.route("/myhouse", methods=["GET", "POST"])
@login_required
def myhouse():
    '''
    This lists the members of the house and the points that they each have 
    '''
    if not current_user.houseId:
        return redirect(url_for("whathouse"))
    # TODO only allow the admin user to see the invites
    invitesWaiting = {}
    for invite in Invite.query.filter_by(houseId=current_user.houseId, isResponded=False).all():
        user = User.query.filter_by(id=invite.idUserInvited).first()
        # TODO understand why prefix is necessary, without it both forms are submitted together
        invitesWaiting[user] = ReplyInviteForm(prefix="{}".format(user.username))
    for invUser, invForm in invitesWaiting.items():
        if invForm.validate_on_submit():
            invite = Invite.query.filter_by(houseId=current_user.houseId, idUserInvited=invUser.id, isResponded=False).first()
            invite.isResponded = True
            if invForm.submitAccept.data:
                invUser.houseId = current_user.houseId
            if invForm.submitDecline.data:
                # TODO send the user a message about the invite being declined?
                pass
            db.session.commit()
            return redirect(url_for("myhouse"))

    return render_template('myhouse.html', invites=invitesWaiting)


@app.route("/whathouse")
@login_required
def whathouse():
    '''
    Choose to either create a house or join an existing one 
    '''
    if current_user.houseId:
        return redirect(url_for("home"))
    open_invite = checkWaitingOnInvite(current_user)
    house_name = None
    if open_invite:
        house_name = House.query.filter_by(id=open_invite.houseId).first().name
    return render_template('whathouse.html', pending_invite=house_name)

# TODO make this a decorator 
def checkWaitingOnInvite(userWaiting):
    # TODO if filter by isResponded then can drop the loop
    for sent_invite in Invite.query.filter_by(idUserInvited=userWaiting.id).all():
        if not sent_invite.isResponded:
            return sent_invite

@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    '''
    Form for creating a house 
    '''
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
    return render_template('create.html', form=houseForm)


@app.route("/join", methods=["GET", "POST"])
@login_required
def join():
    '''
    Join a house by name
    '''
    if current_user.houseId:
        return redirect(url_for("home"))
    # If the user has an ongoing invite, don't let them send another one
    if checkWaitingOnInvite(current_user):
        flash("Already waiting to join a house. Wait for response before trying to join another", "info")
        return redirect(url_for("whathouse"))
    join_form = JoinHouseForm()
    if join_form.validate_on_submit():
        house = House.query.filter_by(name=join_form.name.data).first()
        new_invite = Invite(houseId=house.id, idUserInvited=current_user.id)
        db.session.add(new_invite)
        # current_user.houseId = house.id
        db.session.commit()
        flash(f"Requested to join {join_form.name.data}!", "success")
        return redirect(url_for("whathouse"))
    return render_template('join.html', form=join_form)


@app.route("/newtask", methods=["GET", "POST"])
@login_required
def newtask():
    if not current_user.houseId:
        return redirect(url_for("whathouse"))
    taskForm = NewTaskForm()
    if taskForm.validate_on_submit():
        task = Task(houseId=current_user.houseId, name=taskForm.name.data, 
                    description=taskForm.description.data, value=taskForm.value.data, 
                    coolOffPeriod=taskForm.coolOffPeriod.data, coolOffValue=taskForm.coolOffValue.data
                )
        db.session.add(task)
        db.session.commit()
        flash(f"Task '{taskForm.name.data}' created!", "success")
        return redirect(url_for("home"))

    return render_template('newtask.html', form=taskForm)
