from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField, IntegerField, TextAreaField, \
    SelectField
from wtforms.validators import DataRequired, ValidationError, Length

from .models import Position


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Submit")


class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    second_name = StringField("Second_name", validators=[DataRequired()])
    last_name = StringField("Last_name", validators=[DataRequired()])
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email")
    phone = StringField("Phone", validators=[DataRequired()])
    internal_phone = StringField("Internal_phone", validators=[DataRequired()])
    description = StringField("Description")
    department = SelectField('Department', validators=[DataRequired()], coerce=int)
    position = SelectField('Position', choices=Position.choices(), validators=[DataRequired()], coerce=int)
    role = SelectField('Role', validators=[DataRequired()], coerce=int)

    password= PasswordField("Password", validators=[DataRequired()])
    password_replay = PasswordField("Password_replay", validators=[DataRequired()])

    submit = SubmitField("Submit")

    def __init__(self, departments, positions, roles, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.name.data = user.name
            self.second_name.data = user.second_name
            self.last_name.data = user.last_name
            self.username.data = user.username
            self.phone.data = user.phone
            self.internal_phone.data = user.internal_phone
            self.description.data = user.description
            self.department.default = (user.department.id, user.department.name)
            self.position.data = user.position.id
            self.role.default = (user.role.id, user.role.name)

        self.department.choices = [(department.id, department.name) for department in departments]
        # self.position.choices = [(department.id, department.name) for department in positions]
        self.role.choices = [(role.id, role.name) for role in roles]


class SearchForm(FlaskForm):
    file_name = StringField("File name")
    size_from = IntegerField("Size from")
    size_to = IntegerField("Size to")
    submit = SubmitField("Submit")

    def validate_size_from(self, size_from):

        if size_from.data is None or self.size_to.data is None or size_from.data > self.size_to.data:
            raise ValidationError('Size from must be more than size to')

class OrderComputerForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=255)], render_kw={"autocomplete": "off"})
    description = TextAreaField("Description", validators=[DataRequired(), Length(max=2048)],
                                render_kw={"rows": 3, "cols": 50})

    def __init__(self, order=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if order:
            self.title.data = order.name
            self.description.data = order.description



class ConsultationForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=255)], render_kw={"autocomplete": "off"})
    description = TextAreaField("Description", validators=[DataRequired(), Length(max=2048)],
                                render_kw={"rows": 4, "cols": 50})
    organization = StringField("Organization", validators=[DataRequired(), Length(max=255)],
                               render_kw={"autocomplete": "off"})
    submit = SubmitField("Submit")


class GroupOrderForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=255)], render_kw={"autocomplete": "off"})
    description = TextAreaField("Description", validators=[Length(max=512)], render_kw={"rows": 3, "cols": 50})
    users_performer = SelectField('Users', validators=[DataRequired()], coerce=int)
    submit = SubmitField("Submit")

    def __init__(self, users_performer, group_order=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if group_order:
            self.title.data = group_order.name
            self.description.data = group_order.description

        self.users_performer.choices = [(user.id, user.full_name) for user in users_performer]

class GroupOrderResultForm(FlaskForm):
    title = TextAreaField("Title", validators=[DataRequired(), Length(max=255)], render_kw={"rows": 3, "cols": 50})
    positive = BooleanField("Positive")
    submit = SubmitField("Submit")

    def __init__(self, group_order=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if group_order:
            self.title.data = group_order.name
            self.positive.data = group_order.positive
