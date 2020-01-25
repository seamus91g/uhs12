from flask import render_template, url_for, flash, redirect, request
from flask_login import current_user, login_required
from uhs12app import app, db, bcrypt, mail
from uhs12app.tasks.forms import (
    NewTaskForm,
)
from uhs12app.models import User, House, Invite, Task, TaskLog, ShamePost
from flask import Blueprint

tasks = Blueprint('tasks', __name__)

@tasks.route("/")
@tasks.route("/home", methods=["GET", "POST"])
@login_required
def home():
    """
    The home page will contain your list of tasks
    """
    if not current_user.houseId:
        return redirect(url_for("house.whathouse"))
    allTasks = Task.query.filter_by(houseId=current_user.houseId)
    return render_template("home.html", tasks=allTasks)


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
    return redirect(url_for("tasks.home"))



@tasks.route("/taskdelete", methods=["GET", "POST"])
@login_required
def taskdelete():
    taskLogItem = TaskLog.query.filter_by(id=int(request.args["taskid"])).first()
    nameDeleted = taskLogItem.task.name
    db.session.delete(taskLogItem)
    db.session.commit()
    flash(f"You deleted task '{nameDeleted}'", "info")
    return redirect(url_for("tasks.tasklog"))

