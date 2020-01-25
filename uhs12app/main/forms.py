from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import SubmitField
from wtforms.validators import DataRequired



class NewShamePostForm(FlaskForm):
    picture = FileField('Upload picture evidence', validators=[DataRequired(), FileAllowed(['jpg', 'png'])])

    submit = SubmitField("Cast shame!")

