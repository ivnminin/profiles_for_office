import os, logging, uuid
from functools import wraps
from datetime import datetime

from flask import render_template, request, redirect, url_for, flash, abort, send_file, after_this_request,\
    make_response, jsonify
from werkzeug.utils import secure_filename
from flask_login import login_required, login_user,current_user, logout_user

from app import app
from .models import db, User, Order, GroupOrder, File
from .forms import LoginForm, SearchForm


logging.basicConfig(filename="pydrop.log", level=logging.INFO)
log = logging.getLogger('pydrop')


def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.role.name == "admin":
            return f(*args, **kwargs)
        else:
            flash("You need to be an admin to view this page.")
            return redirect(url_for('index'))

    return wrap


def moderator_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if current_user.role.name == "moderator" or current_user.role.name == "admin":
            return f(*args, **kwargs)
        else:
            flash("You need to be an moderator to view this page.")
            return redirect(url_for('index'))

    return wrap


@app.route('/login/', methods=['post', 'get'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter(User.username == form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('index'))

        flash("Invalid username/password", 'error')
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
    return render_template('my_computer_orders.html', orders=current_user.orders)


@app.route('/computer-orders')
@login_required
def computer_orders():

    orders = db.session.query(Order).all()

    return render_template('computer_orders.html', orders=orders)


@app.route('/computer-order/<id>')
@login_required
def computer_order(id):

    order = db.session.query(Order).filter(Order.id == id).first_or_404()

    return render_template('computer_order.html', order=order)


@app.route('/add-computer-order')
@login_required
def add_computer_order():

    return render_template('add_computer_order.html')


@app.route('/group-orders')
@login_required
def group_orders():

    group_orders = db.session.query(GroupOrder).all()

    return render_template('group_orders.html', group_orders=group_orders)


@app.route('/group-order/<id>')
@login_required
def group_order(id):

    group_order = db.session.query(GroupOrder).filter(GroupOrder.id == id).first_or_404()

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
    return render_template('my_consultations.html', consultations=current_user.consultations)


@app.route('/add-consultation')
@login_required
def add_consultation():
    return render_template('add_consultation.html')


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


@app.route('/download/<file_hash>')
@login_required
def download(file_hash):
    file = db.session.query(File).filter(File.hash == file_hash).first_or_404()
    path_to_file = file.path

    @after_this_request
    def lock_access(response):
        access = FileAccess(file_id=file.id, user_id=current_user.id)
        db.session.add(access)
        db.session.commit()

        return response

    # #FIXME rattle - if you have very more clicks on download button. it's problem.
    # access = FileAccess(file_id=file.id, user_id=current_user.id)
    # db.session.add(access)
    # db.session.commit()

    return send_file(path_to_file, as_attachment=True, cache_timeout=0)


@app.route('/file-card/<hash_id>')
@login_required
def file_card(hash_id):
    file = db.session.query(File).filter(File.hash == hash_id).first_or_404()

    return render_template('file_card.html', file=file)

@app.route('/file-upload/')
@login_required
def file_upload():
    return render_template('file_upload.html')


@app.route('/upload', methods=['POST'])
@login_required
def upload():
    # need for debug
    # # Route to deal with the uploaded chunks
    # log.info(request.form)
    # log.info(request.files)

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

    tmp_path = os.path.join(sub_folder, secure_filename(original_filename))
    _, file_extension = os.path.splitext(tmp_path)
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
        if os.path.getsize(path_to_file) != int(request.form['dztotalfilesize']):
            log.error("File {} was completed, but has a size mismatch. "
                      "Was {} but we expected {} "
                      .format(original_filename, os.path.getsize(path_to_file), request.form['dztotalfilesize']))
            return make_response(('Size mismatch', 500))
        elif current_chunk + 1 > app.config['DROPZONE_MAX_FILES']: return make_response(('Not valid, {}'.format(total_chunks), 500))
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

    else:
        log.debug('Chunk {} of {} for file {} complete {}'
                  .format(current_chunk + 1, total_chunks, original_filename, request.form))

    return make_response(('Chunk upload successful', 200))


# @app.route('/search/', methods=['GET', 'POST'])
# @login_required
# def search():
#
#     found_files = None
#     was_search = False
#     form = SearchForm()
#     if form.validate_on_submit():
#         file_name = form.file_name.data
#         size_from = form.size_from.data
#         size_to = form.size_to.data
#
#         if size_from > size_to:
#             abort(404)
#         was_search = True
#         find_file = '{}%'.format(file_name)
#
#         if size_to and file_name:
#             found_files = db.session.query(File).filter(
#                 File.original_name.like(find_file) &
#                 (File.total_size >= size_from) &
#                 (File.total_size <= size_to)).all()
#         elif size_to and not file_name:
#             found_files = db.session.query(File).filter(
#                 (File.total_size >= size_from) &
#                 (File.total_size <= size_to)).all()
#         elif file_name:
#             found_files  = db.session.query(File).filter(File.original_name.like(find_file)).all()
#
#
#     return render_template('search.html', form=form, files=found_files, was_search=was_search)


# @app.route('/upload', methods=['POST'])
# def handle_upload():
#
#     print('this')
#     for key, f in request.files.items():
#         if key.startswith('file'):
#             f.save(os.path.join(app.config['UPLOADED_PATH'], f.filename))
#     return '', 204
#
#
@app.route('/form', methods=['POST'])
@login_required
def handle_form():

    title = request.form.get('title')
    description = request.form.get('description')

    if not title or not description:
        return jsonify(result='error', errors={'title': 'error_title', 'description': 'error_description'}), 404

    order = Order(name=title, description=description, user=current_user)

    db.session.add(order)
    db.session.commit()

    return jsonify(result='success', data={'title': title, 'description': description, 'order': order.id,
                                           'url':url_for('computer_orders')}), 200


@app.errorhandler(404)
def http_404_handler(error):
    return "<p>HTTP 404 Error Encountered</p>", 404


@app.errorhandler(500)
def http_500_handler(error):
    return "<p>HTTP 500 Error Encountered</p>", 500
