from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, TextAreaField, SelectMultipleField, SelectField, RadioField, FormField, FloatField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')
    

class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')


class AddProjectForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    group = SelectField('Which student group should participate?', validators=[DataRequired()])
    dataset = SelectField('Which dataset will the project work on?', validators=[DataRequired()])
    submit = SubmitField("Create Project")

class FilterForm(FlaskForm):
    included_words = StringField('Words that documents must contain (separate by comma):')
    excluded_words = StringField('Words that documents must NOT contain (separate by comma):')
    test_filter = SubmitField("Try this set of filters")

class CreateFilteredCollectionForm(FlaskForm):
    collection_name = StringField('Name of new collection')
    create_new_collection = SubmitField("Create new collection with these filters")

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