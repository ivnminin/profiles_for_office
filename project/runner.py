import click

from flask_script import Manager, Shell
from flask_migrate import MigrateCommand

from app import app, db
from app.models import Role, User, Position, Organization, Department, Order, GroupOrder, Service, Result, File, Note, \
    Consultation

manager = Manager(app)


@app.shell_context_processor
def make_shell_context():
    return dict(app=app, db=db, Role=Role, User=User, Position=Position, Organization=Organization,
                Department=Department, Order=Order, GroupOrder=GroupOrder, Service=Service, Result=Result,
                File=File, Note=Note, Consultation=Consultation)

manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@app.cli.command('start-project')
def start_project():
    """
    start project start-project >>>db.create_all()
    """
    db.create_all()


@app.cli.command('create-role')
def create_role():
    """
    flask project create-role
    """
    Role.insert_roles()


@app.cli.command('fake-data')
def fake_data():
    """
    flask fake-data
    """

    # if not Role.query.first():
    #     create_role()

    r_a = db.session.query(Role).filter(Role.name == 'admin').first()
    r_m = db.session.query(Role).filter(Role.name == 'moderator').first()
    r_u = db.session.query(Role).filter(Role.name == 'user').first()

    desc = 'Lorem ipsum dolor sit amet, consectetuer adipiscing elit. Aenean commodo ligula eget dolor. Aenean massa. '\
           'Cum sociis natoque penatibus et'

    o = Organization(name='OOO Organization of Project', description=desc)

    d = Department(name='Group of accountants', description=desc)
    d.organization = o

    d1 = Department(name='Group of lawyers', description=desc)
    d1.organization = o

    d2 = Department(name='Administrators', description=desc)
    d2.organization = o

    admin_user = User(name='Pety', second_name='Petrovich', last_name='Petrov', username='admin',
                      email='admin@admin.admin', description='it is admin')
    admin_user.set_password('pass')
    admin_user.department = d2
    admin_user.role = r_a

    p = Position(name='Accountant', description=desc)
    p1 = Position(name='Lawyer', description=desc)

    u = User(name='Ivan', second_name='Ivanovich', last_name='Ivanov', username='ivan', email='ivan@ivan.ivan',
             description=desc)
    u.set_password('pass')
    u.department = d
    u.position = p
    u.role = r_u

    u1 = User(name='Vladimir', second_name='Vladimirovich', last_name='Ivanov', username='vova', email='vova@vova.vova',
             description=desc)
    u1.set_password('pass')
    u1.department = d1
    u1.position = p1
    u1.role = r_m

    ord_ = Order(name='Problems with access to the Internet', description=desc)
    ord_.user = u
    ord1 = Order(name='The printer is not working', description=desc)
    ord1.user = u1

    db.session.add_all([ord_, ord1])
    db.session.commit()

    g = GroupOrder(name='General problem', description=desc)
    g.user_performer = admin_user

    ord_.group_order = g
    ord1.group_order = g

    db.session.add_all([ord_, ord1])
    db.session.commit()

    s = Service(name='The Internet', description=desc)
    s1 = Service(name='Copying and copying equipment', description=desc)
    g.services.append(s)
    g.services.append(s1)

    db.session.add_all([g, g])
    db.session.commit()

    r = Result(name='Performance of equipment', description='it is ok')
    g.results.append(r)
    r1 = Result(name='A small salary for a system administrator', description='It is necessary to increase the salary '
                                                                              'of the system administrator')
    r1.positive = True
    g.results.append(r1)

    db.session.add_all([g, g])
    db.session.commit()

    n = Note(name='some note')
    n1 = Note(name='some note 1')
    n2 = Note(name='Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the'
                   ' industry\'s standard dummy text ever since the 1500s, when an unknown printer took a galley of '
                   'type and scrambled it to make a type specimen book.')

    c = Consultation(name='Lorem Ipsum is simply dummy text of the printing and typesetting industry',
                     description='Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem '
                                  'Ipsum has been the industry\'s standard dummy text ever since the 1500s, when an '
                                  'unknown printer took a galley of type and scrambled it to make a type specimen bok.',
                     organization='Some Organization')

    admin_user.notes.append(n)
    admin_user.notes.append(n1)
    admin_user.notes.append(n2)
    admin_user.consultations.append(c)

    db.session.add_all([admin_user])
    db.session.commit()


@app.cli.command('registration-user')
@click.argument('name')
@click.argument('second_name')
@click.argument('last_name')
@click.argument('username')
@click.argument('password')
def registration_user(name, second_name, last_name, username, password):
    """
    registration user registration-user - <user_name> <password>
    """

    user = User(name=name, second_name=second_name, last_name=last_name, username=username)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()


@app.cli.command('fake-files')
@click.argument('count_files')
@click.argument('user_name')
def files_generation(count_files, user_name):
    """
    file generation - fake-files <count_files> <user_name>
    """
    import uuid, os
    from fpdf import FPDF

    user = db.session.query(User).filter(User.username == user_name).first_or_404()

    files_store_folder = app.config['FILES_STORE_FOLDER']

    for _ in range(int(count_files)):
        hsh = uuid.uuid4().hex
        file_name = hsh + '.pdf'
        sub_folder_name = hsh[0:2]
        sub_folder = os.path.join(files_store_folder, sub_folder_name)
        if not os.path.exists(sub_folder):
            os.mkdir(sub_folder)

        path_to_file = '{folder}/{name}'.format(folder=sub_folder, name=file_name)
        print(path_to_file)

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt='file name: {name}'.format(name=file_name), ln=1, align="C")
        pdf.output(path_to_file)

        file = File(original_name=file_name, hash=hsh, user_id=user.id, path=path_to_file,
                    total_size=os.path.getsize(path_to_file))

        db.session.add(file)
        db.session.commit()


if __name__ == '__main__':
    manager.run()
