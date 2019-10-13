'''
Models for uhs12
'''
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from uhs12app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    '''
    User login model
    '''
    id = Column(Integer, primary_key=True)
    # User may not yet have joined a house, thus nullable is true
    houseId = Column(Integer, ForeignKey("house.id"), nullable=True)
    # Username should actually just be unique per house TODO: how to enforce this? 
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(60), nullable=False)
    profilePic = Column(String(120), nullable=False, default="default.jpg")

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

class House(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(20), nullable=False)
    # TODO Make this a foreign key
    adminId = Column(Integer, nullable=False)
    dateCreated = Column(DateTime, nullable=False, default=datetime.utcnow)
    members = relationship("User", backref="whaat", lazy=True)
    shamePosts = relationship("ShamePost", backref="wtf_is_this", lazy=True)


class Invite(db.Model):
    id = Column(Integer, primary_key=True)
    houseId = Column(Integer, ForeignKey("house.id"), nullable=False)
    idUserInvited = Column(Integer, ForeignKey("user.id"), nullable=False)
    isResponded = Column(Boolean, nullable=False, default=False)

class Task(db.Model):
    id = Column(Integer, primary_key=True)
    houseId = Column(Integer, ForeignKey("house.id"), nullable=False)
    name = Column(String(20), nullable=False)
    description = Column(String(140))
    value = Column(Integer, nullable=False)
    coolOffPeriod = Column(Integer, nullable=False, default=0)
    coolOffValue = Column(Integer, nullable=False, default=0)

    # Function to see if cool off is active 
    def isCooloffActive(self):
        # TODO implement
        return False

    def lastCompletedDate(self):
        # TODO implement
        return "2019-10-15"

    def lastCompletedPerson(self):
        # TODO implement
        return "Bill"


class TaskLog(db.Model):
    id = Column(Integer, primary_key=True)
    houseId = Column(Integer, ForeignKey("house.id"), nullable=False)
    taskId = Column(Integer, ForeignKey("task.id"), nullable=False)
    task = relationship("Task", backref="taskCompleted")
    idUser = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User", backref="taskOwner")
    dateCreated = Column(DateTime, nullable=False, default=datetime.utcnow)
    value = Column(Integer, nullable=False)

    @staticmethod
    def pointsByUser(session, user):
        tasksByuser = session.query(TaskLog).filter_by(idUser=user.id).all()
        totalPts = sum([task.value for task in tasksByuser])
        return totalPts
    
    @classmethod
    def pointsAllUsers(cls, session):
        allUsers = session.query(User).all()
        ptsByUser = {}
        for user in allUsers:
            ptsByUser[user] = cls.pointsByUser(session, user)
        return ptsByUser

#  Db schema
# # # # # # # # 
#   User                id hid^     username        mail                password    dateCreated         
#   House               id          dateCreated     adminUserId         <User>      <ShamePost>
#   WaitingInvites      id hid      idUserInvited   responded
#   Task                id hid      name            description         value       coolDownTime        coolDownValue
#   TaskLog             id hid      taskId          userId              date        
# 
#   ShamePost           id hid      userCreated     photo               comment     disapprovalCount    date
##   ShameComments      id hid      shameLogId      user                comment     date


#### Notes
# <blah> means a relationship
# id = primary key 
# nid = non primary key id 
# disapprovalCount is a bunch of taps, like claps on medium.com
# Two hash at start means it's for future, not now 

# Details in task tab
# Normal
# name, value

# Normal open
# name, description, value, coolDownValue, coolDownTime, last completed and by who

# Cool
# name, coolDownValue, coolDownIsActive

# Cool open
# Same as (Normal open) but with coolDownIsActive


###########################
class ShamePost(db.Model):
    id = Column(Integer, primary_key=True)
    houseId = Column(Integer, ForeignKey("house.id"), nullable=False)
    userId = Column(Integer, nullable=False)
    # TODO: Don't allow default because it should never happen
    postImage = Column(String(20), nullable=False, default="default.jpg")
    comment = Column(String(140))
    # TODO: this should be some kind of date format, not String
    disapprovalCount = Column(Integer, nullable=False, default=0)
    datePosted  = Column(String(20))


