from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, ValidationError, Optional
from flask_login import current_user
from uhs12app.models import Task




class NewTaskForm(FlaskForm):
    name = StringField("Task name", validators=[DataRequired(), Length(min=2, max=20)])
    description = StringField("Task instructions", validators=[Length(min=0, max=140)])
    value = IntegerField(
        "Number of points for completing the task", validators=[DataRequired()]
    )
    coolOffPeriod = IntegerField(
        "Number of cool off days for the task. The task is worth less points during this time",
        validators=[Optional()],
    )
    coolOffValue = IntegerField(
        "Number of points for completing the task during the cool off period",
        validators=[Optional()],
    )

    submit = SubmitField("Create Task")

    def validate_name(self, name):
        newTask = Task.query.filter_by(name=name.data, houseId=current_user.activeHouseId).first()
        if newTask:
            raise ValidationError(
                "That task name is taken. Please choose a different name."
            )
    
    #### @staticmethod
    #### # What the heck? Sometimes it's a tuple and sometimes a list ... ?!?!?!
    #### # TODO make this a decorator
    # def err_tuple_to_list(form_item):
    #     if isinstance(form_item.errors, tuple):
    #         form_item.errors = list(form_item.errors)

    ######## # For some reason, the second method below will not work the same as the first. WTF
    
    #### def validate_coolOffValue(self, coolOffValue):
    ####     if coolOffValue.data and not self.coolOffPeriod.data:
    ####         NewTaskForm.err_tuple_to_list(self.coolOffPeriod)
    ####         err_msg = "If you set a cool off value, you must also set number of cool off days! Leave both blank if you don't want a cool off period."
    ####         self.coolOffPeriod.errors.append(err_msg)
    ####         print("Cool value: ", self.coolOffPeriod.errors)

    # Ensure coolOffValue if there is a coolOffPeriod
    # def validate_coolOffPeriod(self, coolOffPeriod):
    #     if coolOffPeriod.data and not self.coolOffValue.data:
    #         NewTaskForm.err_tuple_to_list(self.coolOffValue)
    #         err_msg = "If you set cool off days, you must also set a cool off value! Leave both blank if you don't want a cool off period."
    #         self.coolOffValue.errors.append(err_msg)
    #         print("cool period: ", self.coolOffValue.errors)

