from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, PasswordField, IntegerField, TextAreaField, \
    SelectField
from wtforms.validators import DataRequired, ValidationError, Length


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Submit")


class SearchForm(FlaskForm):
    file_name = StringField("File name")
    size_from = IntegerField("Size from")
    size_to = IntegerField("Size to")
    submit = SubmitField("Submit")

    def validate_size_from(self, size_from):

        if size_from.data is None or self.size_to.data is None or size_from.data > self.size_to.data:
            raise ValidationError('Size from must be more than size to')

class OrderComputerForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=255)],
                        render_kw={"autocomplete": "off"})
    description = TextAreaField("Description", validators=[DataRequired(), Length(max=2048)],
                                render_kw={"rows": 3, "cols": 50})

    def __init__(self, order=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if order:
            self.title.data = order.name
            self.description.data = order.description



class ConsultationForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=255)])
    description = StringField("Description",)
    organization = StringField("Organization", validators=[DataRequired(), Length(max=255)])
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

        self.users_performer.choices = [(user.id, '{} {} {}'.format(user.name, user.second_name, user.last_name))
                                        for user in users_performer]

class GroupOrderResultForm(FlaskForm):
    title = TextAreaField("Title", validators=[DataRequired(), Length(max=255)], render_kw={"rows": 3, "cols": 50})
    positive = BooleanField("Positive")
    submit = SubmitField("Submit")

    def __init__(self, group_order=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if group_order:
            self.title.data = group_order.name
            self.positive.data = group_order.positive
