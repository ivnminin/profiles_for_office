import os, logging, uuid
from functools import wraps
from datetime import datetime
from slugify import slugify_url, slugify_filename

from flask import render_template, request, redirect, url_for, flash, abort, send_file, after_this_request,\
    make_response, jsonify, session
from werkzeug.utils import secure_filename
from flask_login import login_required, login_user, current_user, logout_user

from app import app, csrf
from .models import db, Role, User, Organization, Department, Position, Order, GroupOrder, File, Consultation, \
    ThemeConsultation, Result, Version
from .forms import LoginForm, SearchForm, OrderComputerForm, ConsultationForm, ThemeConsultationForm, \
    GroupOrderForm, GroupOrderResultForm, UserForm, ChangePasswordForm, DepartmentForm, PositionForm, VersionForm, \
    AnalyticConsultationsForm
from .tasker import send_email


logging.basicConfig(filename="pydrop.log", level=logging.INFO)
log = logging.getLogger('pydrop')


def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.role.name == "admin":
            return f(*args, **kwargs)
        else:
            flash("Для просмотра этой страницы вам необходимо быть администратором.")
            return redirect(url_for('index'))

    return wrap


def moderator_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.role.name == "moderator" or current_user.role.name == "admin":
            return f(*args, **kwargs)
        else:
            flash("Для просмотра этой страницы вам необходимо быть модератором.")
            return redirect(url_for('index'))

    return wrap


def speaker_consultations_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.role.name == "speaker_consultations" or current_user.role.name == "moderator" \
                or current_user.role.name == "admin":
            return f(*args, **kwargs)
        else:
            flash("Для просмотра этой страницы вам необходимо быть аналитиком отчётов по консультациям.")
            return redirect(url_for('index'))

    return wrap


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter(User.username == form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('index'))

        flash("Неверное имя пользователя или пароль", 'error')
        return redirect(url_for('login'))

    return render_template('login.html', form=form)


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.")
    return redirect(url_for('login'))


@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)


@app.route('/my-computer-orders')
@login_required
def my_computer_orders():

    filter = request.args.get('filter')
    if filter == 'new':
        orders = db.session.query(Order).filter(Order.user == current_user, Order.group_order == None)\
                                        .order_by(db.desc(Order.created_on)).all()
    elif filter:
        orders = db.session.query(Order)\
            .filter(Order.user==current_user, Order.group_order).join(GroupOrder).filter(GroupOrder.status==filter)\
            .order_by(db.desc(Order.created_on)).all()
    else:
        orders = current_user.orders

    return render_template('my_computer_orders.html', orders=orders)


@app.route('/computer-orders')
@login_required
def computer_orders():

    filter = request.args.get('filter')
    if filter == 'new':
        orders = db.session.query(Order).filter(Order.group_order == None)\
                                        .order_by(db.desc(Order.created_on)).all()
    elif filter:
        orders = db.session.query(Order)\
            .filter(Order.group_order).join(GroupOrder).filter(GroupOrder.status==filter)\
            .order_by(db.desc(Order.created_on)).all()
    else:
        orders = db.session.query(Order).order_by(db.desc(Order.created_on)).all()

    return render_template('computer_orders.html', orders=orders)


@app.route('/computer-order/<id>', methods=['GET', 'POST'])
@login_required
def computer_order(id):

    order = db.session.query(Order).filter(Order.id == id).first_or_404()
    if current_user.is_moderator:
        group_orders = db.session.query(GroupOrder).filter((GroupOrder.status == app.config['STATUS_TYPE']['in_work'])|
                                                           (GroupOrder.status == app.config['STATUS_TYPE']['cancelled']))\
                                                   .order_by(db.desc(GroupOrder.created_on)).all()

        return render_template('computer_order.html', order=order, group_orders=group_orders)

    return render_template('computer_order.html', order=order)


@app.route('/add-computer-order')
@login_required
def add_computer_order():
    form = OrderComputerForm()
    return render_template('add_computer_order.html', form=form)


@app.route('/edit-computer-order/<id>')
@login_required
def edit_computer_order(id):

    order = db.session.query(Order).filter(Order.id == id, Order.user==current_user,
                                           Order.group_order == None).first_or_404()
    form = OrderComputerForm(order)

    return render_template('edit_computer_order.html', form=form, order=order)


@app.route('/group-orders')
@login_required
def group_orders():

    filter = request.args.get('filter')
    if filter == 'new':
        group_orders = db.session.query(GroupOrder).filter(GroupOrder.status == None)\
                                                   .order_by(db.desc(GroupOrder.created_on)).all()
    elif filter:
        group_orders = db.session.query(GroupOrder)\
                                 .filter(GroupOrder.status==filter)\
                                 .order_by(db.desc(GroupOrder.created_on)).all()
    else:
        group_orders = db.session.query(GroupOrder).order_by(db.desc(GroupOrder.created_on)).all()


    return render_template('group_orders.html', group_orders=group_orders)


@app.route('/group-order/<id>', methods=['GET', 'POST'])
@app.route('/group-order/<id>/<result_id>', methods=['GET', 'POST'])
@login_required
def group_order(id, result_id=None):

    group_order = db.session.query(GroupOrder).filter(GroupOrder.id == id).first_or_404()
    if current_user.is_moderator:

        if result_id:
            result =  db.session.query(Result).filter(Result.id == result_id).first_or_404()

            if request.method == 'GET':
                form = GroupOrderResultForm(result)
            else:
                form = GroupOrderResultForm()

            if form.validate_on_submit():
                result.name = form.title.data,
                result.positive = form.positive.data
                db.session.add(result)
                db.session.commit()

                flash("Группа заявок изменена.", 'success')
                return redirect(url_for('group_order', id=id))

            return render_template('group_order.html', group_order=group_order, form=form)

        else:
            form = GroupOrderResultForm()
            if form.validate_on_submit():

                result = Result(name=form.title.data, positive=form.positive.data)
                group_order.results.append(result)

                db.session.add(group_order)
                db.session.commit()

                flash("Группа заявок создана.", 'success')
                return redirect(url_for('group_order', id=id))

            return render_template('group_order.html', group_order=group_order, form=form)

    return render_template('group_order.html', group_order=group_order)


@app.route('/email-orders')
@login_required
def email_orders():
    return render_template('email_orders.html')


@app.route('/my-email-orders')
@login_required
def my_email_orders():
    return render_template('my_email_orders.html')


@app.route('/add-email-order')
@login_required
def add_email_order():
    return render_template('add_email_order.html')


@app.route('/resources')
@login_required
def resources():
    return render_template('resources.html')


@app.route('/notes')
@login_required
def notes():
    return render_template('my_notes.html', notes=current_user.notes)


@app.route('/add-note')
@login_required
def add_note():
    return render_template('add_note.html')


@app.route('/consultations')
@login_required
def consultations():

    consultations = db.session.query(Consultation).order_by(db.desc(Consultation.created_on)).all()

    return render_template('consultations.html', consultations=consultations)


@app.route('/group-consultations')
@login_required
def group_consultations():

    consultations = db.session.query(Consultation).join(User).filter(User.department==current_user.department) \
                                                  .order_by(db.desc(Consultation.created_on)).all()

    return render_template('consultations.html', consultations=consultations, next_page='group-consultations')


@app.route('/my-consultations')
@login_required
def my_consultations():

    consultations = db.session.query(Consultation).filter(Consultation.user==current_user)\
                                                  .order_by(db.desc(Consultation.created_on)).all()

    return render_template('consultations.html', consultations=consultations, next_page='my-consultations')


@app.route('/add-consultation', methods=['GET', 'POST'])
@app.route('/add-consultation/<id>', methods=['GET', 'POST'])
@login_required
def add_consultation(id=None):

    mode = None
    next_pages = {'group-consultations': 'group_consultations', 'my-consultations': 'my_consultations', }
    next_page = next_pages.get(request.args.get('next_page'), 'consultations')

    if id:
        mode = True
        consultation = db.session.query(Consultation).filter(Consultation.id == id).first_or_404()

        if not current_user.position.chief or current_user.department != consultation.user.department:
            abort(404)

        if request.method == 'GET':
            form = ConsultationForm(consultation)
        else:
            form = ConsultationForm()

        if request.method == 'POST' and form.validate_on_submit():

            consultation.name = form.title.data
            consultation.description = form.description.data
            consultation.organization = form.organization.data
            consultation.reg_number = form.reg_number.data
            consultation.person = form.person.data

            db.session.add(consultation)
            db.session.commit()

            flash("Консультация изменена.", 'success')
            return redirect(url_for(next_page))
    else:
        form = ConsultationForm()
        if form.validate_on_submit():

            consultation = Consultation(name=form.title.data,
                                        description=form.description.data,
                                        organization=form.organization.data,
                                        reg_number=form.reg_number.data,
                                        person=form.person.data,
                                        user=current_user,
                                        )

            db.session.add(consultation)
            db.session.commit()

            flash("Консультация создана.", 'success')
            return redirect(url_for(next_page))

    return render_template('add_consultation.html', form=form, mode=mode)


@app.route('/change-status-consultation/<id>', methods=['GET'])
@login_required
def change_status_consultation(id):

    consultation = db.session.query(Consultation).filter(Consultation.id == id).first_or_404()

    if not current_user.position.chief or current_user.department != consultation.user.department:
        abort(404)

    next_pages = {'group-consultations': 'group_consultations', 'my-consultations': 'my_consultations', }
    next_page = next_pages.get(request.args.get('next_page'), 'consultations')

    status = request.args.get('status')
    if status == 'off':
        consultation.status = False
    else:
        consultation.status = True

    db.session.add(consultation)
    db.session.commit()

    flash("Статус изменён", 'success')
    return redirect(url_for(next_page))


@app.route('/analytic-consultations', methods=['GET', 'POST'])
@login_required
@speaker_consultations_required
def analytic_consultations():

    consultations = None

    form = AnalyticConsultationsForm()
    if form.validate_on_submit():

        flash("Отчёт создан.", 'success')
        return redirect(url_for('analytic_consultations', form=form, consultations=consultations))

    return render_template('analytic_consultations.html', form=form, consultations=consultations)


@app.route('/recommendations')
@login_required
def recommendations():
    return render_template('my_recommendations.html')


@app.route('/add-recommendation')
@login_required
def add_recommendation():
    return render_template('add_recommendation.html')


@app.route('/admin-page')
@login_required
@admin_required
def admin_page():
    return render_template('admin.html')


@app.route('/moderator-page')
@login_required
@moderator_required
def moderator_page():
    return render_template('moderator.html')


@app.route('/moderator-page/computer-orders')
@login_required
@moderator_required
def moderator_page_computer_orders():
    return redirect(url_for('computer_orders'))


@app.route('/moderator-page/add-user', methods=['GET', 'POST'])
@app.route('/moderator-page/add-user/<id>', methods=['GET', 'POST'])
@login_required
@moderator_required
def moderator_page_add_user(id=None):

    users = db.session.query(User).order_by(db.desc(User.created_on)).all()
    mode = None
    if id:

        user = db.session.query(User).filter(User.id == id).first_or_404()
        mode = user

        if request.method == 'GET':
            form = UserForm(mode, user)
        else:
            form = UserForm(mode)

        if request.method == 'POST' and form.validate_on_submit():

            department = db.session.query(Department).filter(Department.id==form.department.data).first()
            position = db.session.query(Position).filter(Position.id==form.position.data).first()
            role = db.session.query(Role).filter(Role.id==form.role.data).first()

            user.name = form.name.data
            user.second_name = form.second_name.data
            user.last_name = form.last_name.data
            user.username = form.username.data
            user.email = form.email.data
            user.phone = form.phone.data
            user.internal_phone = form.internal_phone.data
            user.description = form.description.data

            user.department = department
            user.position = position
            user.role = role

            db.session.add(user)
            db.session.commit()

            flash("Пользователь изменён.", 'success')
            return redirect(url_for('moderator_page_add_user'))
    else:
        form = UserForm(mode)
        if form.validate_on_submit():

            department = db.session.query(Department).filter(Department.id==form.department.data).first()
            position = db.session.query(Position).filter(Position.id==form.position.data).first()
            role = db.session.query(Role).filter(Role.id==form.role.data).first()

            user = User(name=form.name.data,
                        second_name=form.second_name.data,
                        last_name=form.last_name.data,
                        username=form.username.data,
                        email=form.email.data,
                        phone=form.phone.data,
                        internal_phone=form.internal_phone.data,
                        description=form.description.data,)

            user.set_password(form.password.data)
            user.department = department
            user.position = position
            user.role = role

            db.session.add(user)
            db.session.commit()

            flash("Пользователь создан.", 'success')
            return redirect(url_for('moderator_page_add_user'))

    return render_template('moderator_page_add_user.html', form=form, users=users, mode=mode)


@app.route('/moderator-page/change-password/<id>', methods=['GET', 'POST'])
@login_required
@moderator_required
def moderator_page_change_password(id):

    user = db.session.query(User).filter(User.id == id).first_or_404()

    form = ChangePasswordForm()
    if request.method == 'POST' and form.validate_on_submit():

        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Пароль сохранён.", 'success')
        return redirect(url_for('moderator_page_add_user'))

    return render_template('moderator_page_change_password.html', form=form, user=user)


@app.route('/moderator-page/add-department', methods=['GET', 'POST'])
@app.route('/moderator-page/add-department/<id>', methods=['GET', 'POST'])
@login_required
@moderator_required
def moderator_page_add_department(id=None):

    departments = db.session.query(Department).all()
    mode = None

    if id:
        mode = True
        department = db.session.query(Department).filter(Department.id == id).first_or_404()

        if request.method == 'GET':
            form = DepartmentForm(department)
        else:
            form = DepartmentForm()

        if request.method == 'POST' and form.validate_on_submit():

            department.name = form.name.data

            db.session.add(department)
            db.session.commit()

            flash("Наименование группу изменено.", 'success')
            return redirect(url_for('moderator_page_add_department'))
    else:
        form = DepartmentForm()
        if form.validate_on_submit():

            organization = db.session.query(Organization).first()
            department = Department(name=form.name.data)
            organization.departments.append(department)

            db.session.add(organization)
            db.session.commit()

            flash("Наименование группу создано.", 'success')
            return redirect(url_for('moderator_page_add_department'))

    return render_template('moderator_page_add_department.html', form=form, departments=departments, mode=mode)


@app.route('/moderator-page/add-position', methods=['GET', 'POST'])
@app.route('/moderator-page/add-position/<id>', methods=['GET', 'POST'])
@login_required
@moderator_required
def moderator_page_add_position(id=None):

    positions = db.session.query(Position).all()
    mode = None

    if id:
        mode = True
        position = db.session.query(Position).filter(Position.id == id).first_or_404()

        if request.method == 'GET':
            form = PositionForm(position)
        else:
            form = PositionForm()

        if request.method == 'POST' and form.validate_on_submit():
            position.name = form.name.data
            position.chief = form.chief.data

            db.session.add(position)
            db.session.commit()

            flash("Наименование позиции изменено.", 'success')
            return redirect(url_for('moderator_page_add_position'))
    else:
        form =PositionForm()
        if form.validate_on_submit():

            position = Position(name=form.name.data, chief=form.chief.data)

            db.session.add(position)
            db.session.commit()

            flash("Наименование позиции создано.", 'success')
            return redirect(url_for('moderator_page_add_position'))

    return render_template('moderator_page_add_position.html', form=form, positions=positions, mode=mode)


@app.route('/moderator-page/add-theme-consultation', methods=['GET', 'POST'])
@app.route('/moderator-page/add-theme-consultation/<id>', methods=['GET', 'POST'])
@login_required
@moderator_required
def moderator_page_add_theme_consultation(id=None):

    theme_consultations = db.session.query(ThemeConsultation).all()
    mode = None

    if id:
        mode = True
        theme_consultation = db.session.query(ThemeConsultation).filter(ThemeConsultation.id == id).first_or_404()

        if request.method == 'GET':
            form = ThemeConsultationForm(theme_consultation)
        else:
            form = ThemeConsultationForm()

        if request.method == 'POST' and form.validate_on_submit():
            theme_consultation.name = form.name.data

            db.session.add(theme_consultation)
            db.session.commit()

            flash("Тема консультации изменена.", 'success')
            return redirect(url_for('moderator_page_add_theme_consultation'))
    else:
        form = ThemeConsultationForm()
        if form.validate_on_submit():

            theme_consultation = ThemeConsultation(name=form.name.data)

            db.session.add(theme_consultation)
            db.session.commit()

            flash("Тема консультации создана.", 'success')
            return redirect(url_for('moderator_page_add_theme_consultation'))

    return render_template('moderator_page_add_theme_consultation.html', form=form,
                           theme_consultations=theme_consultations, mode=mode)


@app.route('/moderator-page/add-group-order', methods=['GET', 'POST'])
@app.route('/moderator-page/add-group-order/<id>', methods=['GET', 'POST'])
@login_required
@moderator_required
def moderator_page_add_group_order(id=None):

    users_performer = db.session.query(Role).filter(Role.name=='moderator').first().users
    group_orders = db.session.query(GroupOrder).order_by(db.desc(GroupOrder.created_on)).all()

    if id:
        group_order = db.session.query(GroupOrder).filter(GroupOrder.id == id).first_or_404()
        if request.method == 'GET':
            form = GroupOrderForm(users_performer, group_order)
        else:
            form = GroupOrderForm(users_performer)

        if request.method == 'POST' and form.validate_on_submit():
            user_performer = db.session.query(User).filter(User.id==form.users_performer.data).first_or_404()
            group_order.name = form.title.data,
            group_order.description = form.description.data
            group_order.user_performer = user_performer
            db.session.add(group_order)
            db.session.commit()

            flash("Группа заявок изменена.", 'success')
            return redirect(url_for('moderator_page_add_group_order'))
    else:
        form = GroupOrderForm(users_performer)
        if form.validate_on_submit():

            user_performer = db.session.query(User).filter(User.id==form.users_performer.data).first_or_404()
            group_order = GroupOrder(name=form.title.data, description=form.description.data,
                                     user_performer=user_performer)
            db.session.add(group_order)
            db.session.commit()

            flash("Группа заявок создана.", 'success')
            return redirect(url_for('moderator_page_add_group_order'))

    return render_template('moderator_page_add_group_order.html', form=form, group_orders=group_orders)


@app.route('/moderator-page/moderator-page-fix-group-order/<order_id>/<group_order_id>/')
@login_required
@moderator_required
def moderator_page_fix_group_order(order_id, group_order_id):

    order = db.session.query(Order).filter(Order.id == order_id).first_or_404()
    group_order = db.session.query(GroupOrder).filter(GroupOrder.id == group_order_id).first_or_404()

    group_order.orders.append(order)

    db.session.add(group_order)
    db.session.commit()

    flash("Заявка добавлена в группу.", 'success')
    return redirect(url_for('moderator_page_computer_orders'))


@app.route('/moderator-page/group-orders')
@login_required
@moderator_required
def moderator_page_group_orders():

    return redirect(url_for('group_orders'))


@app.route('/moderator-page/group-order/<id>/select-status/')
@login_required
@moderator_required
def moderator_page_group_order_select_status(id):
    group_order = db.session.query(GroupOrder).filter(GroupOrder.id == id).first_or_404()
    status = request.args.get('status')

    if status and status in app.config['STATUS_TYPE']:

        if status == app.config['STATUS_TYPE']['closed'] and not any(result.positive for result in group_order.results):
            flash("Group order was not closed", 'alert')
            return redirect(url_for('group_order', id=id))
        else:
            group_order.status = status
            db.session.add(group_order)
            db.session.commit()
            flash("Статус группы заявок изменён.", 'success')
            return redirect(url_for('group_order', id=id))

    abort(404)


@app.route('/moderator-page/add-version', methods=['GET', 'POST'])
@app.route('/moderator-page/add-version/<id>', methods=['GET', 'POST'])
@login_required
@moderator_required
def moderator_page_add_version(id=None):
    versions = db.session.query(Version).all()
    mode = None

    if id:
        mode = True
        version = db.session.query(Version).filter(Version.id == id).first_or_404()

        if request.method == 'GET':
            form = VersionForm(version)
        else:
            form = VersionForm()

        if request.method == 'POST' and form.validate_on_submit():
            version.version = form.version.data
            version.user_description = form.user_description.data
            version.admin_description = form.admin_description.data

            db.session.add(version)
            db.session.commit()

            flash("Версия ПО обновлена", 'success')
            return redirect(url_for('moderator_page_add_version'))
    else:
        form = VersionForm()
        if form.validate_on_submit():
            version = Version(version=form.version.data,
                              user_description=form.user_description.data,
                              admin_description=form.admin_description.data,)

            db.session.add(version)
            db.session.commit()

            flash("Версия ПО создана.", 'success')
            return redirect(url_for('moderator_page_add_version'))

    return render_template('moderator_page_add_version.html', form=form, versions=versions, mode=mode)


@app.route('/files-list/', methods=['GET', 'POST'])
@login_required
def files_list():
    page = request.args.get('page', 1, type=int)
    per_page = app.config['FILES_PER_PAGE']

    # files = db.session.query(File).limit(per_page).offset((page - 1) * per_page).all()

    files = File.query.paginate(page, per_page, False)

    next_url = url_for('files_list', page=files.next_num) if files.has_next else None
    prev_url = url_for('files_list', page=files.prev_num) if files.has_prev else None

    return render_template('files_list.html', files=files.items, next_url=next_url, prev_url=prev_url)



@app.route('/upload', methods=['POST'])
@csrf.exempt
@login_required
def upload():

    title = request.form.get('title')
    description = request.form.get('description')
    order_id = request.form.get('order_id')

    log.info('Start title: {} description: {} order_id:'.format(title, description, order_id))

    files_store_folder = app.config['UPLOADED_PATH']
    today_year = datetime.now().strftime('%Y')
    files_store_folder = os.path.join(files_store_folder, today_year)
    try:
        os.mkdir(files_store_folder)
    except FileExistsError:
        pass

    hsh = request.form['dzuuid']

    file = request.files['file']
    original_filename = file.filename

    # I think keeping all the files in one folder is a bad idea.
    sub_folder_name = datetime.now().strftime('%d-%m-%Y')
    sub_folder = os.path.join(files_store_folder, sub_folder_name)
    try:
        os.mkdir(sub_folder)
    except FileExistsError:
        pass

    original_filename_after_slug = slugify_filename(original_filename)

    tmp_path = os.path.join(sub_folder, secure_filename(original_filename_after_slug))
    _, file_extension = os.path.splitext(tmp_path)
    if not file_extension:
        file_extension = '.no_file_extension'
    new_file_name = hsh + file_extension
    path_to_file = '{folder}/{name}'.format(folder=sub_folder, name=new_file_name)

    current_chunk = int(request.form['dzchunkindex'])

    # If the file already exists it's ok if we are appending to it,
    # but not if it's new file that would overwrite the existing one
    if os.path.exists(path_to_file) and current_chunk == 0:
        # 400 and 500s will tell dropzone that an error occurred and show an error
        return make_response(('File already exists', 400))

    try:
        with open(path_to_file, 'ab') as f:
            f.seek(int(request.form['dzchunkbyteoffset']))
            f.write(file.stream.read())
    except OSError:
        # log.exception will include the traceback so we can see what's wrong
        log.exception('Could not write to file')
        return make_response(('Not sure why, but we couldn\'t write the file to disk', 500))

    total_chunks = int(request.form['dztotalchunkcount'])

    if current_chunk + 1 == total_chunks:
        # This was the last chunk, the file should be complete and the size we expect
        if os.path.getsize(path_to_file) != int(request.form['dztotalfilesize']) \
                or os.path.getsize(path_to_file) > app.config['UPLOADED_MAX_FILES']:
            log.error("File {} was completed, but has a size mismatch. "
                      "Was {} but we expected {} "
                      .format(original_filename, os.path.getsize(path_to_file), request.form['dztotalfilesize']))
            return make_response(('Size mismatch', 500))
        else:
            log.info('File {} has been uploaded successfully. total_chunks {}'.format(original_filename, total_chunks))

            hsh = uuid.uuid4().hex
            new_file = '{folder}/{name}'.format(folder=sub_folder, name=hsh + file_extension)
            os.rename(path_to_file, new_file)

            log.info('File {} has been renamed to {}'.format(original_filename, new_file))

            order = db.session.query(Order).filter(Order.id == order_id).first()

            # if not order: return make_response(('Not exist order', 500))

            file = File(original_name=original_filename, hash=hsh, path=new_file,
                        total_size=os.path.getsize(new_file))

            order.files.append(file)

            db.session.add(order)
            db.session.commit()

            if len(order.files) > app.config['DROPZONE_MAX_FILES']:
                return make_response(('Not valid, {}'.format(len(order.files)), 500))

    else:
        log.debug('Chunk {} of {} for file {} complete {}'
                  .format(current_chunk + 1, total_chunks, original_filename, request.form))

    return make_response(('Chunk upload successful', 200))


@app.route('/form', methods=['POST'])
@login_required
def handle_form():

    form = OrderComputerForm()

    if not form.validate_on_submit():

        return jsonify(result='error', errors={'title': form.title.errors, 'description': form.description.errors}), 404

    title = request.form.get('title')
    description = request.form.get('description')
    order_id = request.form.get('order')

    if order_id:
        order = db.session.query(Order).filter(Order.id == int(order_id)).first_or_404()
        if order.group_order:
            return jsonify(result='error',
                           errors={'error_msg': 'you can not edit this order, sorry'}), 404

        order.name = title
        order.description = description

        flash("Заявка изменена.", 'success')
    else:
        order = Order(name=title, description=description, user=current_user)

        flash("Заявка создана.", 'success')

    db.session.add(order)
    db.session.commit()

    try:
        send_email.apply_async(args=[order.id, app.config['MAIL_USERNAME'], [app.config['MAIL_ADMIN'], ]], countdown=3)
    except Exception as e:
        log.error('Function send_email.apply_async has some problems, error: {}'.format(e))

    return jsonify(result='success', data={'title': title, 'description': description, 'order': order.id,
                                           'url':url_for('computer_orders')}), 200


@app.route('/download/<file_hash>')
@login_required
def download(file_hash):

    file = db.session.query(File).filter(File.hash == file_hash).first_or_404()
    path_to_file = file.path

    return send_file(path_to_file, as_attachment=True, cache_timeout=0)


@app.route('/delete-order-files/<id>')
@login_required
def delete_order_files(id):

    order = db.session.query(Order).filter(Order.id == id,
                                           Order.user==current_user, Order.group_order == None).first_or_404()

    for file in order.files:
        db.session.delete(file)
        db.session.commit()

    flash("Файлы были удалены.", 'success')
    return redirect(url_for('edit_computer_order', id=order.id))


@app.route('/moderator-computer-orders')
@login_required
@moderator_required
def moderator_computer_orders():

    orders = db.session.query(Order).order_by(db.desc(Order.created_on)).all()

    return render_template('moderator_computer_orders.html', orders=orders)


@app.route('/versions')
@login_required
def versions():

    versions = db.session.query(Version).order_by(db.desc(Version.created_on)).all()

    return render_template('versions.html', versions=versions)


@app.errorhandler(404)
def http_404_handler(error):
    return "<p>HTTP 404 Error Encountered</p>", 404


@app.errorhandler(500)
def http_500_handler(error):
    return "<p>HTTP 500 Error Encountered</p>", 500


@app.route('/open-page', methods=['GET', 'POST'])
@csrf.exempt
def open_page():
    response = ''

    for key, value in request.headers.items():
        response = response + key + ': ' + value +'<br>'

    c = '<br>Your cookies: <br>'
    for key, value in request.cookies.items():
        c = c + key + ': ' + value +'<br>'

    s = '<br>Your sessions (client session because it is Flask): <br>'
    for key, value in session.items():
        s = s + key + ': ' + str(value) + '<br>'

    response = response + c + s

    res = make_response(response)
    res.set_cookie('foo', 'bar', max_age=60 * 60 * 24 * 365 * 2)
    res.set_cookie('foo1', 'bar1')

    # if session.get('visits'):
    #     return str(print(session))
    # else:
    session['visits'] = 2

    print(session)

    return res
