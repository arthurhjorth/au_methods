from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, TextAreaField, SelectMultipleField, SelectField, RadioField, FormField, FloatField, HiddenField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from wtforms.widgets import TextArea

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
    student_group = SelectField('Which group are you in?', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class HistogramForm2(FlaskForm):
    data = SelectField('Which data do you want to see a histogram of?', validators=[DataRequired()])
    reflections = TextAreaField('What do you expect to find? How will this help you answer your larger questions?', validators=[DataRequired()])
    submit_histogram = SubmitField("Create histogram")


class AddProjectForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    group = SelectField('Which student group should participate?', validators=[DataRequired()])
    dataset = SelectField('Which dataset will the project work on?', validators=[DataRequired()])
    submit = SubmitField("Create Project")

class LinearRegressionForm2(FlaskForm):
    x_heading = SelectField('Choose data for your X axis (Number data only)', validators=[DataRequired()])
    y_heading = SelectField('Choose data for your Y axis (Number data only)', validators=[DataRequired()])
    reflections = TextAreaField('What do you expect to find? How will this help you answer your larger questions?', validators=[DataRequired()])
    submit_linear_regression = SubmitField("Do a Linear Regression on these Data")


class TTestForm(FlaskForm):
    collection1 = SelectField('Select the first collection you want to do a T-Test on', validators=[DataRequired()])
    collection2 = SelectField('Select the second collection you want to do a T-Test on', validators=[DataRequired()])
    submit_collections = SubmitField("Choose these collections")

class TTestForm2(FlaskForm):
    data1 = SelectField('Choose the first set of data for your t-test', validators=[DataRequired()])
    data2 = SelectField('Choose the second set of data for your t-test', validators=[DataRequired()])
    reflections = TextAreaField('What do you expect to find? How will this help you answer your larger questions?', validators=[DataRequired()])
    submit_ttest = SubmitField("Do a T-Test of these two sets of data")

class LinearRegressionForm(FlaskForm):
    collection = SelectField('Choose the collection you want to do a linear regression on', validators=[DataRequired()])
    submit_collections = SubmitField("Choose this collection")

class ApplyFunctionForm(FlaskForm):
    field_name = SelectField('Which field do you want to apply the function to?', validators=[DataRequired()])
    function = SelectField('What kind of function?', validators=[DataRequired()])
    reasoning = StringField('Tell us what information you are hoping to find with this analysis. What do you expect to find? Why is it relevant for this collection of documents?')
    apply_function = SubmitField("Apply this function")

class FilterForm2(FlaskForm):
    field_name = SelectField('Which field do you want to filter on?', validators=[DataRequired()])
    operator = SelectField('What kind of filter?', validators=[DataRequired()])
    filter_data = StringField('How do you want to filter?')
    add_filter = SubmitField("Add this filter")
    name_of_new_collection = StringField("What is the name of your new collection?")
    apply_filter = SubmitField("Try all these filters")

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