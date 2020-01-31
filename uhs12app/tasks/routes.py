from flask import render_template, url_for, flash, redirect, request
from flask_login import current_user, login_required
from uhs12app import db, bcrypt, mail
from uhs12app.tasks.forms import (
    NewTaskForm,
)
from uhs12app.models import User, House, Invite, Task, TaskLog, ShamePost, TaskRequest, TaskClaim
from flask import Blueprint

tasks = Blueprint('tasks', __name__)

class TaskBoardInfo(object):
    """Info about the taskboard on the home screen"""
    def __init__(self, house_id):
        allTasks = Task.query.filter_by(houseId=house_id)
        # Sort the tasks with an open request first 
        allTaskRequests = TaskRequest.query.filter_by(houseId=house_id, isExpired=False).all()
        allTaskClaims = TaskClaim.query.filter_by(houseId=house_id, isExpired=False).all()
        allTaskRequests = TaskRequest.updateExpired(allTaskRequests)
        allTaskClaims = TaskRequest.updateExpired(allTaskClaims)
        # Check if any tasks or claims are expired. Store in dict for easy lookups 
        self.allTaskRequests = {taskReq.taskId: taskReq for taskReq in allTaskRequests}
        self.allTaskClaims = {taskClaim.taskId: taskClaim for taskClaim in allTaskClaims}
        self.allTasks = sorted(allTasks, key=lambda x : self.allTaskRequests.get(x.id) is not None and self.allTaskClaims.get(x.id) is None, reverse=True)

    def request_id(self, task):
        return self.allTaskRequests.get(task.id).id if self.allTaskRequests.get(task.id) else None

    # ID of an open claim made on the task
    def claim_id(self, task):
        return self.allTaskClaims.get(task.id).id if self.allTaskClaims.get(task.id) else None

    # ID of the user who has an open claim on the task
    def claimer_id(self, task):
        return self.allTaskClaims.get(task.id).userClaimed.id if self.allTaskClaims.get(task.id) else None

    # Return true if the given user has an open claim on the task 
    def has_user_claimed(self, user, task):
        return user.id == self.claimer_id(task)

    # ID of the user who has an open request on the task 
    def requester_id(self, task):
        return self.allTaskRequests.get(task.id).userId if self.allTaskRequests.get(task.id) else None
    
    # Return true if the given user has an open request on the task 
    def has_user_requested(self, user, task):
        return user.id == self.requester_id(task)
    
    def has_other_user_claimed(self, user, task):
        # False if there's no open claim
        if not self.claim_id(task):
            return False
        # False if this user has a claim
        if self.claimer_id(task) == user.id:
            return False
        # Another user must have an open claim 
        return True

@tasks.route("/")
@tasks.route("/home", methods=["GET", "POST"])
@login_required
def home():
    """
    The home page will contain your list of tasks
    """
    if not current_user.houseId:
        return redirect(url_for("house.whathouse"))
    task_info = TaskBoardInfo(current_user.houseId)
    db.session.commit()    # TODO is this commit needed? To update expired?
    return render_template("home.html", task_info=task_info, curr_user=current_user)


@tasks.route("/taskrequest", methods=["GET", "POST"])
@login_required
def taskrequest():
    # Create a request
    taskRequested = Task.query.filter_by(id=int(request.args["taskid"])).first()
    newRequest = TaskRequest(
        houseId=current_user.houseId,
        taskId=taskRequested.id,
        userId=current_user.id,
    )
    db.session.add(newRequest)
    db.session.commit()
    flash(f"You've made a request for task '{taskRequested.name}'!", "success")
    return redirect(url_for("tasks.home"))



@tasks.route("/taskclaim", methods=["GET", "POST"])
@login_required
def taskclaim():
    taskClaimed = Task.query.filter_by(id=int(request.args["taskid"])).first()
    # Create a claim 
    newClaim = TaskClaim(
        houseId=current_user.houseId,
        taskId=taskClaimed.id,
        userId=current_user.id,
    )
    db.session.add(newClaim)
    db.session.commit()
    flash(f"Great! You've claimed '{taskClaimed.name}' for 1 day", "success")
    return redirect(url_for("tasks.home"))



@tasks.route("/newtask", methods=["GET", "POST"])
@login_required
def newtask():
    if not current_user.houseId:
        return redirect(url_for("house.whathouse"))
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
        return redirect(url_for("tasks.home"))

    return render_template("newtask.html", form=taskForm)


@tasks.route("/tasklog")
@login_required
def tasklog():
    page_num = request.args.get('page', 1, type=int)
    allTasksCompleted = TaskLog.query.order_by(TaskLog.dateCreated.desc()).filter_by(houseId=current_user.houseId).paginate(per_page=20, page=page_num)
    return render_template(
        "tasklog.html", tasklog=allTasksCompleted, currUser=current_user
    )

@tasks.route("/taskcomplete", methods=["GET", "POST"])
@login_required
def taskcomplete():
    if request.args.get("claimid"):
        # TODO isExpired filter is pointless here, how could we get here with an expired one? 
        # TODO this should only ever be one item, ensure this is correct
        claims = TaskClaim.query.filter_by(id=int(request.args["claimid"]), isExpired=False).all()
        for claim in claims: 
            claim.isExpired = True
    if request.args.get("requestid"):
        taskRequests = TaskRequest.query.filter_by(id=int(request.args["requestid"]), isExpired=False).all()
        for taskReq in taskRequests: 
            taskReq.isExpired = True
    taskCompleted = Task.query.filter_by(id=int(request.args["taskid"])).first()
    # TODO if last completed date is with cool off window, value is cool off value
    taskItem = TaskLog(
        houseId=current_user.houseId,
        taskId=taskCompleted.id,
        idUser=current_user.id,
        value=taskCompleted.currentValue(),
        coolOff=taskCompleted.isCooloffActive(),
    )
    db.session.add(taskItem)
    db.session.commit()
    taskCompleted.setLastCompleted(current_user, taskItem.dateCreated)
    flash(f"Great work! You completed task '{taskCompleted.name}'", "success")
    db.session.commit()
    return redirect(url_for("tasks.home"))


@tasks.route("/taskdelete", methods=["GET", "POST"])
@login_required
def taskdelete():
    taskLogItem = TaskLog.query.filter_by(id=int(request.args["taskid"])).first()
    nameDeleted = taskLogItem.task.name
    db.session.delete(taskLogItem)
    # Update last completed time of task
    # If date doesn't match, doesn't need updating
    task = Task.query.filter_by(id=taskLogItem.taskId).first()
    if task.lastCompletedDate == taskLogItem.dateCreated:
        task.refreshLastCompleted()
    db.session.commit()
    flash(f"You deleted task '{nameDeleted}'", "info")
    return redirect(url_for("tasks.tasklog"))

