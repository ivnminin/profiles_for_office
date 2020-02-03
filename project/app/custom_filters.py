from jinja2 import environment

def generate_custom_filter(app):

    def view_status(value):

        if app.config['STATUS_TYPE']['in_work'] == value:
            return 'В работе'

        elif app.config['STATUS_TYPE']['closed'] == value:
            return 'Закрыта'

        elif app.config['STATUS_TYPE']['cancelled'] == value:
            return 'Отменена'

        return 'Новая'

    def first_symbols(value, count_symbols=None):
        c = count_symbols or 255

        dots = ''
        if len(value) > c:
            dots = ' ...'

        new_value = '{}{}'.format(value[0:c], dots)

        return new_value

    environment.DEFAULT_FILTERS['view_status'] = view_status
    environment.DEFAULT_FILTERS['first_symbols'] = first_symbols