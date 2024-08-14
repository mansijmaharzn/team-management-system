from django.core.mail import send_mail
from celery import shared_task


@shared_task
def send_email_task(subject, message, from_email, recipient_list):
    send_mail(
        subject,
        message,
        from_email,
        recipient_list,
        fail_silently=False,
    )


# cd team_mgmt_sys
# celery -A team_mgmt_sys flower
# celery -A team_mgmt_sys worker -l info
