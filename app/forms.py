"""WTForms — input validation lives here."""
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    TextAreaField,
    SelectField,
    DateField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Optional,
    ValidationError,
)

from app.models import User


class SignupForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(3, 64)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    role = SelectField(
        "Role",
        choices=[("member", "Member"), ("admin", "Admin")],
        default="member",
    )
    submit = SubmitField("Sign Up")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data.strip()).first():
            raise ValidationError("Username already taken.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.strip().lower()).first():
            raise ValidationError("Email already registered.")


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Log In")


class ProjectForm(FlaskForm):
    name = StringField("Project Name", validators=[DataRequired(), Length(2, 120)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Save")


class AddMemberForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    submit = SubmitField("Add Member")


class TaskForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(2, 160)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=2000)])
    status = SelectField(
        "Status",
        choices=[("todo", "To Do"), ("in_progress", "In Progress"), ("done", "Done")],
        default="todo",
    )
    assignee_id = SelectField("Assignee", coerce=int, validators=[Optional()])
    due_date = DateField("Due Date", validators=[Optional()])
    submit = SubmitField("Save Task")
