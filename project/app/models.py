from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import app, db, login_manager


class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    created_on = db.Column(db.DateTime(), default=datetime.now)
    updated_on = db.Column(db.DateTime(), default=datetime.now,  onupdate=datetime.now)

    users = db.relationship('User', backref='role')

    @classmethod
    def insert_roles(cls):
        for permission in app.config['PERMISSION']:
            role = cls(name=permission)
            db.session.add(role)
            db.session.commit()

    @classmethod
    def choices(cls):
        r = [(role.id, role.name) for role in db.session.query(cls).all()]
        r.append((0, ''))
        return r


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    second_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    internal_phone = db.Column(db.String(50))
    password_hash = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    created_on = db.Column(db.DateTime(), default=datetime.now)
    updated_on = db.Column(db.DateTime(), default=datetime.now,  onupdate=datetime.now)

    department_id = db.Column(db.Integer(), db.ForeignKey('departments.id'), nullable=False)
    role_id = db.Column(db.Integer(), db.ForeignKey('roles.id'), nullable=False)
    position_id = db.Column(db.Integer(), db.ForeignKey('positions.id'), nullable=False)

    orders = db.relationship('Order', backref='user')
    notes = db.relationship('Note', backref='user')
    consultations = db.relationship('Consultation', backref='user')
    theme_consultations = db.relationship('ThemeConsultation', backref='user')
    recommendations = db.relationship('Recommendation', backref='user')
    versions = db.relationship('Version', backref='user')
    performer = db.relationship('GroupOrder', backref='user_performer')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_administrator(self):
        if self.role.name == 'admin':
            return True

    @property
    def is_moderator(self):
        if self.role.name in ['moderator', 'admin']:
            return True

    @property
    def is_speaker_consultations(self):
        if self.role.name in ['speaker_consultations', 'moderator', 'admin']:
            return True

    @property
    def is_user(self):
        if self.role.name == 'user':
            return True

    @property
    def full_name(self):
        return '{} {} {}'.format(self.last_name, self.name, self.second_name)

    def __repr__(self):
        return "<{}:{}>".format(self.id, self.username)


class Position(db.Model):
    __tablename__ = 'positions'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(512), nullable=False, unique=True)
    description = db.Column(db.String(255))
    chief = db.Column(db.Boolean, default=False)
    created_on = db.Column(db.DateTime(), default=datetime.now)
    updated_on = db.Column(db.DateTime(), default=datetime.now,  onupdate=datetime.now)

    users = db.relationship('User', backref='position')

    @classmethod
    def choices(cls):
        r = [(choice.id, choice.name) for choice in db.session.query(cls).all()]
        r.append((0, ''))
        return r


class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(512), nullable=False)
    description = db.Column(db.String(255))
    created_on = db.Column(db.DateTime(), default=datetime.now)
    updated_on = db.Column(db.DateTime(), default=datetime.now,  onupdate=datetime.now)

    departments = db.relationship('Department', backref='organization')


class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))
    created_on = db.Column(db.DateTime(), default=datetime.now)
    updated_on = db.Column(db.DateTime(), default=datetime.now,  onupdate=datetime.now)

    organization_id = db.Column(db.Integer(), db.ForeignKey('organizations.id'))
    users = db.relationship('User', backref='department')

    @classmethod
    def choices(cls):
        r = [(department.id, department.name) for department in db.session.query(cls).all()]
        r.append((0, ''))
        return r


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).get(user_id)


class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(2048))
    created_on = db.Column(db.DateTime(), default=datetime.now)
    updated_on = db.Column(db.DateTime(), default=datetime.now,  onupdate=datetime.now)

    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))


class Consultation(db.Model):
    __tablename__ = 'consultations'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(2048))
    organization = db.Column(db.String(512), nullable=False)
    reg_number = db.Column(db.String(255))
    person = db.Column(db.String(255))
    status = db.Column(db.Boolean, default=True)
    created_on = db.Column(db.DateTime(), default=datetime.now)
    updated_on = db.Column(db.DateTime(), default=datetime.now,  onupdate=datetime.now)

    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))


class ThemeConsultation(db.Model):
    __tablename__ = 'theme_consultations'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.String(255))
    created_on = db.Column(db.DateTime(), default=datetime.now)
    updated_on = db.Column(db.DateTime(), default=datetime.now,  onupdate=datetime.now)

    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))

    @classmethod
    def choices(cls):
        r = [(choice.name, choice.name) for choice in db.session.query(cls).all()]
        r.append(('', ''))
        return r


class Recommendation(db.Model):
    __tablename__ = 'recommendations'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(2048))
    created_on = db.Column(db.DateTime(), default=datetime.now)
    updated_on = db.Column(db.DateTime(), default=datetime.now,  onupdate=datetime.now)

    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(2048), nullable=False)
    created_on = db.Column(db.DateTime(), default=datetime.now)
    updated_on = db.Column(db.DateTime(), default=datetime.now,  onupdate=datetime.now)

    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))
    group_order_id = db.Column(db.Integer(), db.ForeignKey('group_orders.id'))
    files = db.relationship('File', backref='order')


group_order_services = db.Table('group_order_services',
    db.Column('group_order_id', db.Integer, db.ForeignKey('group_orders.id')),
    db.Column('service_id', db.Integer, db.ForeignKey('services.id'))
)


class GroupOrder(db.Model):
    __tablename__ = 'group_orders'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(512))
    status = db.Column(db.String(16),  default=app.config['STATUS_TYPE']['in_work'])
    with_support = db.Column(db.Boolean, default=False)
    created_on = db.Column(db.DateTime(), default=datetime.now)
    updated_on = db.Column(db.DateTime(), default=datetime.now,  onupdate=datetime.now)

    performer_id = db.Column(db.Integer(), db.ForeignKey('users.id'), nullable=False)
    orders = db.relationship('Order', backref='group_order')
    results = db.relationship('Result', backref='group_order')
    services = db.relationship('Service', secondary=group_order_services, backref='group_order')


class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.String(512))
    created_on = db.Column(db.DateTime(), default=datetime.now)
    updated_on = db.Column(db.DateTime(), default=datetime.now,  onupdate=datetime.now)


class Result(db.Model):
    __tablename__ = 'results'

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(8160))
    description = db.Column(db.String(8160))
    positive = db.Column(db.Boolean, default=False)
    created_on = db.Column(db.DateTime(), default=datetime.now)
    updated_on = db.Column(db.DateTime(), default=datetime.now,  onupdate=datetime.now)

    group_order_id = db.Column(db.Integer(), db.ForeignKey('group_orders.id'))


class File(db.Model):
    __tablename__ = 'files'

    id = db.Column(db.Integer, primary_key=True)
    original_name = db.Column(db.String(255), nullable=False)
    hash = db.Column(db.String(255), nullable=False)
    path = db.Column(db.String(255), nullable=False)
    total_size = db.Column(db.Integer, nullable=False)
    timestamp_created = db.Column(db.DateTime, default=datetime.now)

    order_id = db.Column(db.Integer(), db.ForeignKey('orders.id'))

    def __str__(self):
        return self.original_name

    def __repr__(self):
        return "<{}:{}>".format(id, self.original_name)


class Version(db.Model):
    __tablename__ = 'versions'

    id = db.Column(db.Integer(), primary_key=True)
    version = db.Column(db.String(255), nullable=False)
    user_description = db.Column(db.String(2048), nullable=False)
    admin_description = db.Column(db.String(2048), nullable=False)
    created_on = db.Column(db.DateTime(), default=datetime.now)
    updated_on = db.Column(db.DateTime(), default=datetime.now,  onupdate=datetime.now)

    user_id = db.Column(db.Integer(), db.ForeignKey('users.id'))