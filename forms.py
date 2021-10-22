from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, TextAreaField, SelectMultipleField, SelectField, RadioField, FormField, FloatField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

class AddProjectForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    group = SelectField('Which student group should participate?', validators=[DataRequired()])
    dataset = SelectField('Which dataset will the project work on?', validators=[DataRequired()])
    submit = SubmitField("Create Project")

class AddTagForm(FlaskForm):
    tag_names = SelectField('Select Tag', validators=[DataRequired()])
    submit_tag_name = SubmitField("Add Tag to Document")

class CreateTagForm(FlaskForm):
    tag_name = StringField('New Tag Name', validators=[DataRequired()])
    submit_tag_name = SubmitField("Add new Tag")

class AddGroupForm(FlaskForm):
    name = StringField('Group Name', validators=[DataRequired()])
    group = SelectField('Which group is this student', validators=[DataRequired()])

class AddUserForm(FlaskForm):
    name = StringField('Title', validators=[DataRequired()])
    email = StringField('Email', validators=[Email()])
    group = SelectField('Which group is this student', validators=[DataRequired()])

class AddCommentForm(FlaskForm):
    text = TextAreaField('Comment text', validators=[DataRequired()])
    submit_comment = SubmitField("Add Comment")