from app import celery_app
from .models import db, Order
from flask_mail import Message
from app import mail


@celery_app.task
def gen_prime(x):
    multiples = []
    results = []
    for i in range(2, x+1):
        if i not in multiples:
            results.append(i)
            for j in range(i*i, x+1, i):
                multiples.append(j)

    return results


@celery_app.task
def send_email(id, sender, recipients):

    order = db.session.query(Order).filter(Order.id == id).first()

    subject = '№{}, {}'.format(order.id, order.user.full_name)
    body = '{}\n{}\n{}\n{}'.format(subject, order.name, '-'*70, order.description)

    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = body
    # msg.html = html_body
    # if attachments:
    #     for attachment in attachments:
    #         msg.attach(*attachment)

    mail.send(msg)



if __name__ == '__main__':

    pass
