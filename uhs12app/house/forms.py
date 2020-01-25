from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from uhs12app.models import House 


class NewHouseForm(FlaskForm):
    name = StringField("House name", validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField("Create House")

    def validate_name(self, name):
        house = House.query.filter_by(name=name.data).first()
        if house:
            raise ValidationError(
                "That house name is taken. Please choose a different one."
            )


class JoinHouseForm(FlaskForm):
    name = StringField("House name", validators=[DataRequired(), Length(min=2, max=20)])
    submit = SubmitField("Join House")

    def validate_name(self, name):
        house = House.query.filter_by(name=name.data).first()
        if not house:
            raise ValidationError("That house does not exist!")


class ReplyInviteForm(FlaskForm):

    submitAccept = SubmitField("accept")
    submitDecline = SubmitField("decline")
