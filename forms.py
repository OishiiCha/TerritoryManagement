from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, SelectField, FileField, DateTimeField, IntegerField
from wtforms.validators import DataRequired, Email, Optional

class AssignForm(FlaskForm):
    user = SelectField('User', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Assign')

class CheckInForm(FlaskForm):
    submit = SubmitField('Check In')

class UploadForm(FlaskForm):
    pdf_file = FileField('PDF File', validators=[DataRequired()])
    submit = SubmitField('Upload')

class AddMapForm(FlaskForm):
    name = StringField('Map Name', validators=[DataRequired()])
    area = StringField('Area', validators=[DataRequired()])
    submit = SubmitField('Add')

class AddUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[Email()])  # Remove DataRequired() validator to make email optional
    submit = SubmitField('Add')

class UserForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    submit = SubmitField('Add User')

class ImportForm(FlaskForm):
    file = FileField("File", validators=[FileRequired()])
    submit = SubmitField("Import")
    def __repr__(self):
        return f"<User {self.name}>"

class EditHistoryForm(FlaskForm):
    map_id = IntegerField('Map ID', validators=[DataRequired()])
    typecode = IntegerField('Type', validators=[DataRequired()])
    assigned_to = StringField('Assigned To', validators=[DataRequired()])
    assigned_date = DateTimeField('Assigned Date', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()])
    checked_in_date = DateTimeField('Checked In Date', format='%Y-%m-%d %H:%M:%S', validators=[DataRequired()])
    submit = SubmitField('Save Changes')


class RenameMapForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super(RenameMapForm, self).__init__(*args, **kwargs)
        if 'map_name' in kwargs:
            self.name.data = kwargs['map_name']

    name = StringField("New Map Name", validators=[DataRequired()])
    submit = SubmitField("Rename Map")


class ImportForm(FlaskForm):
    file = FileField("CSV File", validators=[
        FileRequired(),
        FileAllowed(['csv'], 'CSV files only!')
    ])
    submit = SubmitField("Import")
