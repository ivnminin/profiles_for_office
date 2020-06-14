from datetime import datetime, timedelta
from jinja2 import environment
from flask import url_for


def generate_custom_filter(app):

    def view_status(value):

        if app.config['STATUS_TYPE']['in_work'] == value:
            return 'В работе'

        elif app.config['STATUS_TYPE']['closed'] == value:
            return 'Закрыта'

        elif app.config['STATUS_TYPE']['cancelled'] == value:
            return 'Отменена'

        return 'Новая'


    def view_status_css(value):

        if app.config['STATUS_TYPE']['in_work'] == value.status:
            today = datetime.now()
            delta = today - timedelta(days=60)
            if value.created_on < delta:
                return app.config['STATUS_TYPE_CSS']['in_work_long']
            elif value.with_support:
                return app.config['STATUS_TYPE_CSS']['with_support']
            return app.config['STATUS_TYPE_CSS']['in_work']
        elif app.config['STATUS_TYPE']['closed'] == value.status:
            return app.config['STATUS_TYPE_CSS']['closed']

        elif app.config['STATUS_TYPE']['cancelled'] == value.status:
            return app.config['STATUS_TYPE_CSS']['cancelled']

        return ''


    def select_status(value, id):

        page = 'moderator_page_group_order_select_status'

        if app.config['STATUS_TYPE']['in_work'] == value:

            url_closed = url_for(page, id=id,
                                 status=app.config['STATUS_TYPE']['closed'])
            url_cancelled = url_for(page, id=id,
                                 status=app.config['STATUS_TYPE']['cancelled'])

            return  """
                        <a href="#" class="warning button">В работе</a>
                        <a href="{}" class="success button hollow">Закрыть</a>
                        <a href="{}" class="secondary button hollow">Отменить</a>
                    """.format(url_closed, url_cancelled)

        elif app.config['STATUS_TYPE']['closed'] == value:

            url_in_work = url_for(page, id=id,
                                  status=app.config['STATUS_TYPE']['in_work'])
            url_cancelled = url_for(page, id=id,
                                     status=app.config['STATUS_TYPE']['cancelled'])

            return  """
                        <a href="{}" class="warning button hollow">В работу</a>
                        <a href="#" class="success button">Закрыта</a>
                        <a href="{}" class="secondary button hollow">Отменить</a>
                    """.format(url_in_work, url_cancelled)

        elif app.config['STATUS_TYPE']['cancelled'] == value:

            url_in_work = url_for(page, id=id,
                                  status=app.config['STATUS_TYPE']['in_work'])
            url_closed = url_for(page, id=id,
                                 status=app.config['STATUS_TYPE']['closed'])

            return  """
                        <a href="{}" class="warning button hollow">В работу</a>
                        <a href="{}" class="success button hollow">Закрыть</a>
                        <a href="#" class="secondary button">Отменена</a>
                    """.format(url_in_work, url_closed)


    def first_symbols(value, count_symbols=None):
        c = count_symbols or 255

        dots = ''
        if len(value) > c:
            dots = ' ...'

        new_value = '{}{}'.format(value[0:c], dots)

        return new_value

    environment.DEFAULT_FILTERS['view_status'] = view_status
    environment.DEFAULT_FILTERS['view_status_css'] = view_status_css
    environment.DEFAULT_FILTERS['select_status'] = select_status
    environment.DEFAULT_FILTERS['first_symbols'] = first_symbols