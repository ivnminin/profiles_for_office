from jinja2 import environment

def generate_custom_filter(app):

    def view_status(value):

        if app.config['STATUS_TYPE']['new'] == value:
            return 'Новая'

        elif app.config['STATUS_TYPE']['in_work'] == value:
            return 'В работе'

        elif app.config['STATUS_TYPE']['closed'] == value:
            return 'Закрыта'

        elif app.config['STATUS_TYPE']['cancelled'] == value:
            return 'Отменена'

        return value

    environment.DEFAULT_FILTERS['view_status'] = view_status