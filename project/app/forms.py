from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField, IntegerField, TextAreaField, \
    SelectField, DateField
from wtforms.validators import DataRequired, ValidationError, Length

from .models import db, User, Department, Position, Role, ThemeConsultation


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(message='Это поле является обязательным.')])
    password = PasswordField("Password", validators=[DataRequired(message='Это поле является обязательным.')])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Submit")


class UserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(message='Это поле является обязательным.')],
                       render_kw={"autocomplete": "off"})
    second_name = StringField("Second_name", validators=[DataRequired(message='Это поле является обязательным.')],
                              render_kw={"autocomplete": "off"})
    last_name = StringField("Last_name", validators=[DataRequired(message='Это поле является обязательным.')],
                            render_kw={"autocomplete": "off"})
    username = StringField("Username", validators=[DataRequired(message='Это поле является обязательным.')],
                           render_kw={"autocomplete": "off"})
    email = StringField("Email", render_kw={"autocomplete": "off"})
    phone = StringField("Phone", validators=[DataRequired(message='Это поле является обязательным.')],
                        render_kw={"autocomplete": "off"})
    internal_phone = StringField("Internal_phone", validators=[DataRequired(message='Это поле является обязательным.')],
                                 render_kw={"autocomplete": "off"})
    description = StringField("Description", render_kw={"autocomplete": "off"})

    department = SelectField('Department', default=0,
                             validators=[DataRequired(message='Это поле является обязательным.')], coerce=int)
    position = SelectField('Position', default=0,
                           validators=[DataRequired(message='Это поле является обязательным.')], coerce=int)
    role = SelectField('Role', default=0, validators=[DataRequired(message='Это поле является обязательным.')],
                       coerce=int)

    password = PasswordField("Password")
    password_replay = PasswordField("Password_replay")

    submit = SubmitField("Submit")

    def validate_password(self, password):
        if not self._mode:
            if not password.data.strip() or password.data != self.password_replay.data:
                raise ValidationError('Пароли не равны или пароль пуст.')

    def validate_username(self, username):
        if not self._mode:
            if db.session.query(User).filter(User.username==username.data).first():
                raise ValidationError('Имя пользователя уже есть.')
        else:
            if self._mode.username != username.data:
                if db.session.query(User).filter(User.username == username.data).first():
                    raise ValidationError('Имя пользователя уже есть')

    def __init__(self, mode, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mode = mode
        self._user = user
        if user:
            self.user_id = user.id
            self.name.data = self._user.name
            self.second_name.data = self._user.second_name
            self.last_name.data = self._user.last_name
            self.username.data = self._user.username
            self.phone.data = self._user.phone
            self.internal_phone.data = self._user.internal_phone
            self.description.data = self._user.description
            self.department.data = self._user.department.id
            self.position.data = self._user.position.id
            self.role.data = self._user.role.id

        self.department.choices = Department.choices()
        self.position.choices = Position.choices()
        self.role.choices = Role.choices()


class ChangePasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired(message='Это поле является обязательным.')])
    password_replay = PasswordField("Password_replay",
                                    validators=[DataRequired(message='Это поле является обязательным.')])
    submit = SubmitField("Submit")

    def validate_password(self, password):
        if password.data != self.password_replay.data:
            raise ValidationError('Passwords are not equal')


class DepartmentForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(message='Это поле является обязательным.')],
                       render_kw={"autocomplete": "off"})
    submit = SubmitField("Submit")

    def __init__(self, department=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if department:
            self.name.data =department.name


class PositionForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(message='Это поле является обязательным.'),
                                           Length(max=512, message='Длина поля не может превышать 512 символов.')],
                                           render_kw={"autocomplete": "off"})
    chief = BooleanField("Positive")
    submit = SubmitField("Submit")

    def __init__(self, position=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if position:
            self.name.data = position.name
            self.chief.data = position.chief


class SearchForm(FlaskForm):
    file_name = StringField("File name")
    size_from = IntegerField("Size from")
    size_to = IntegerField("Size to")
    submit = SubmitField("Submit")

    def validate_size_from(self, size_from):

        if size_from.data is None or self.size_to.data is None or size_from.data > self.size_to.data:
            raise ValidationError('Size from must be more than size to')


class OrderComputerForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(message='Это поле является обязательным.'),
                                             Length(max=255, message='Длина поля не может превышать 250 символов.')],
                        render_kw={"autocomplete": "off"})
    description = TextAreaField("Description", validators=[DataRequired(message='Это поле является обязательным.'),
                                Length(max=2048, message='Длина поля не может превышать 2048 символов.')],
                                render_kw={"rows": 3, "cols": 50})

    def __init__(self, order=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if order:
            self.title.data = order.name
            self.description.data = order.description


class ConsultationForm(FlaskForm):
    title = SelectField("Title", default='', validators=[DataRequired(message='Это поле является обязательным.'),
                        Length(max=255, message='Длина поля не может превышать 250 символов.')],
                        render_kw={"autocomplete": "off"}, coerce=str)
    description = TextAreaField("Description",
                                validators=[Length(max=2048, message='Длина поля не может превышать 2048 символов.')],
                                render_kw={"rows": 4, "cols": 50})
    organization = StringField("Organization",
                               validators=[DataRequired(message='Это поле является обязательным.'),
                               Length(max=255, message='Длина поля не может превышать 250 символов.')],
                               render_kw={"autocomplete": "off"})
    reg_number = StringField("Reg number",
                             validators=[Length(max=255, message='Длина поля не может превышать 250 символов.')],
                             render_kw={"autocomplete": "off"})
    person = StringField("Person", validators=[Length(max=255, message='Длина поля не может превышать 250 символов.')],
                         render_kw={"autocomplete": "off"})

    submit = SubmitField("Submit")

    def __init__(self, consultation=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if consultation:
            self.title.data = consultation.name
            self.description.data = consultation.description
            self.organization.data = consultation.organization
            self.reg_number.data = consultation.reg_number
            self.person.data = consultation.person

        self.title.choices = ThemeConsultation.choices()


class ThemeConsultationForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(message='Это поле является обязательным.'),
                                           Length(max=255, message='Длина поля не может превышать 250 символов.')],
                                           render_kw={"autocomplete": "off"})
    submit = SubmitField("Submit")

    def __init__(self, theme_consultation=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if theme_consultation:
            self.name.data = theme_consultation.name


class AnalyticConsultationsForm(FlaskForm):
    report_date_start = DateField("Report Start Date",
                                  validators=[DataRequired(message='Это поле является обязательным.')],
                                  format="%d-%m-%Y", render_kw={"autocomplete": "off",})
    report_date_finish = DateField("Report Finish Date",
                                   validators=[DataRequired(message='Это поле является обязательным.')],
                                   format="%d-%m-%Y", render_kw={"autocomplete": "off"})
    submit = SubmitField("Submit")

    def validate_report_date_finish(self, report_date_finish):

        if  report_date_finish.data and self.report_date_start.data \
                and report_date_finish.data < self.report_date_start.data:
            raise ValidationError('Дата окончания отчета должна быть позже, чем дата начало отчёта!')




class Form(FlaskForm):
    name = StringField("Name", validators=[DataRequired(message='Это поле является обязательным.'),
                                           Length(max=255, message='Длина поля не может превышать 250 символов.')],
                                           render_kw={"autocomplete": "off"})
    submit = SubmitField("Submit")

    def __init__(self, theme_consultation=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if theme_consultation:
            self.name.data = theme_consultation.name


class GroupOrderForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(message='Это поле является обязательным.'),
                                             Length(max=255, message='Длина поля не может превышать 250 символов.')],
                        render_kw={"autocomplete": "off"})
    description = TextAreaField("Description", validators=[Length(max=512,
                          message='Длина поля не может превышать 512 символов.')], render_kw={"rows": 3, "cols": 50})
    users_performer = SelectField('Users', validators=[DataRequired(message='Это поле является обязательным.')],
                                  coerce=int)
    submit = SubmitField("Submit")

    def __init__(self, users_performer, group_order=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if group_order:
            self.title.data = group_order.name
            self.description.data = group_order.description

        self.users_performer.choices = [(user.id, user.full_name) for user in users_performer]


class GroupOrderResultForm(FlaskForm):
    title = TextAreaField("Title", validators=[DataRequired(message='Это поле является обязательным.'),
                                               Length(max=255, message='Длина поля не может превышать 250 символов.')],
                                               render_kw={"rows": 3, "cols": 50})
    positive = BooleanField("Positive")
    submit = SubmitField("Submit")

    def __init__(self, group_order=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if group_order:
            self.title.data = group_order.name
            self.positive.data = group_order.positive


class VersionForm(FlaskForm):
    version = StringField("User version", validators=[DataRequired(message='Это поле является обязательным.'),
                                            Length(max=255, message='Длина поля не может превышать 250 символов.')],
                                          render_kw={"autocomplete": "off"})
    user_description = TextAreaField("User description",
                                     validators=[DataRequired(message='Это поле является обязательным.'),
                                        Length(max=2048, message='Длина поля не может превышать 2048 символов.')],
                                     render_kw={"autocomplete": "off", "rows": 3, "cols": 50})
    admin_description = TextAreaField("Admin description",
                                      validators=[DataRequired(message='Это поле является обязательным.'),
                                          Length(max=2048, message='Длина поля не может превышать 2048 символов.')],
                                      render_kw={"autocomplete": "off", "rows": 3, "cols": 50})
    submit = SubmitField("Submit")

    def __init__(self, version=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if version:
            self.version.data = version.version
            self.user_description.data = version.user_description
            self.admin_description.data = version.admin_description