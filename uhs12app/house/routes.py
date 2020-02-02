from flask import render_template, url_for, flash, redirect, request
from flask_login import current_user, login_required
from uhs12app import db
from uhs12app.house.forms import (
    NewHouseForm,
    JoinHouseForm,
    ReplyInviteForm,
)
from uhs12app.models import User, House, Invite, TaskLog, Membership

from flask import Blueprint

house = Blueprint('house', __name__)

@house.route("/myhouse", methods=["GET", "POST"])
@login_required
def myhouse():
    """
    This lists the members of the house and the points that they each have 
    """
    if not current_user.activeHouseId:
        return redirect(url_for("house.whathouse"))
    house = House.query.filter_by(id=current_user.activeHouseId).first()
    # TODO only allow the admin user to see the invites
    invitesWaiting = {}
    for invite in Invite.query.filter_by(
        houseId=current_user.activeHouseId, isResponded=False
    ).all():
        user = User.query.filter_by(id=invite.idUserInvited).first()
        # TODO understand why prefix is necessary, without it both forms are submitted together
        invitesWaiting[user] = ReplyInviteForm(prefix="{}".format(user.username))
    for invUser, invForm in invitesWaiting.items():
        if invForm.validate_on_submit():
            invite = Invite.query.filter_by(
                houseId=current_user.activeHouseId,
                idUserInvited=invUser.id,
                isResponded=False,
            ).first()
            invite.isResponded = True
            if invForm.submitAccept.data:
                invUser.activeHouseId = current_user.activeHouseId
                newMembership = Membership(houseId=current_user.activeHouseId, idUser=invUser.id)
                db.session.add(newMembership)
            if invForm.submitDecline.data:
                # TODO send the user a message about the invite being declined?
                pass
            db.session.commit()
            return redirect(url_for("house.myhouse"))
    # TODO make this an OrderedDict and sort by person with most points
    pts_users = TaskLog.pointsAllUsers(db.session, current_user.activeHouseId)
    return render_template("myhouse.html", house=house.name, invites=invitesWaiting, points=pts_users)


@house.route("/whathouse")
@login_required
def whathouse():
    """
    Choose to either create a house or join an existing one 
    """
    if current_user.activeHouseId:
        return redirect(url_for("tasks.home"))
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


@house.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """
    Form for creating a house 
    """
    allow_extra = request.args.get("allowextra")
    if current_user.activeHouseId and not allow_extra:
        return redirect(url_for("tasks.home"))
    if checkWaitingOnInvite(current_user) and not allow_extra:
        flash(
            "Already waiting to join a house. Wait for a response before trying create a new one.",
            "info",
        )
        return redirect(url_for("house.whathouse"))
    houseForm = NewHouseForm()
    if houseForm.validate_on_submit():
        newHouse = House(name=houseForm.name.data, adminId=current_user.id)
        db.session.add(newHouse)
        # newHouse only gets an id after commit, thus we need two commits
        db.session.commit()
        current_user.activeHouseId = newHouse.id
        newMembership = Membership(houseId=newHouse.id, idUser=current_user.id)
        db.session.add(newMembership)
        db.session.commit()
        flash(f"House {houseForm.name.data} created!", "success")
        return redirect(url_for("tasks.home"))
    return render_template("create.html", form=houseForm)


@house.route("/join", methods=["GET", "POST"])
@login_required
def join():
    """
    Join a house by name
    """
    allow_extra = request.args.get("allowextra")
    if current_user.activeHouseId and not allow_extra:
        return redirect(url_for("tasks.home"))
    # If the user has an ongoing invite, don't let them send another one
    if checkWaitingOnInvite(current_user) and not allow_extra:
        # TODO make sure this can expire so user can try join another
        flash(
            "Already waiting to join a house. Wait for response before trying to join another.",
            "info",
        )
        return redirect(url_for("house.whathouse"))
    join_form = JoinHouseForm()
    if join_form.validate_on_submit():
        house = House.query.filter_by(name=join_form.name.data).first()
        if not house:
            flash(f"No house exists with that name!", "info")
            return redirect(url_for("house.whathouse"))
        if not house.active_memberships():
            # If a house is empty, and previous member can join freely
            membership = Membership.query.filter_by(houseId=house.id, idUser=current_user.id).first()
            memall = Membership.query.filter_by().all()
            if membership:
                current_user.activeHouseId = house.id
                newMembership = Membership(houseId=house.id, idUser=current_user.id)
                db.session.add(newMembership)
                db.session.commit()
                flash(f"You have joined {house.name}!", "success")
                return redirect(url_for("house.myhouse"))
            flash(f"That house is not accepting new members!", "info")
            return redirect(url_for("house.whathouse"))
        new_invite = Invite(houseId=house.id, idUserInvited=current_user.id)
        db.session.add(new_invite)
        db.session.commit()
        flash(f"Requested to join {join_form.name.data}!", "success")
        return redirect(url_for("house.whathouse"))
    return render_template("join.html", form=join_form)


@house.route("/leavehouse", methods=["GET", "POST"])
@login_required
def leavehouse():
    """
    Remove current user from a house. 
    We do this by setting the membership to expired. 
    The user's active house is set to a random other one which they 
    are a member of, or None if they are in no other houses. 
    """
    expired_house_id = int(request.args.get("houseid"))
    assert current_user.activeHouseId == expired_house_id
    for membrship in current_user.active_memberships():
        if membrship.houseId == expired_house_id:
            membrship.isExpired = True
    if current_user.active_memberships():
        # Assign random other one, doesn't matter which
        current_user.activeHouseId = current_user.active_memberships()[0].houseId
        return redirect(url_for("house.myhouse"))
    current_user.activeHouseId = None
    db.session.commit()
    return redirect(url_for("house.whathouse"))