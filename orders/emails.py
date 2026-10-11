from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

from .models import Order


def send_order_confirmation(order: Order) -> None:
    if not order.user.email:
        return
    body = render_to_string(
        "orders/email/order_confirmation.txt", {"order": order, "site_domain": settings.SITE_DOMAIN}
    )
    send_mail(
        subject=f"Velore — замовлення {order.number} оформлено",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
        fail_silently=True,
    )


def send_status_update(order: Order) -> None:
    if not order.user.email:
        return
    body = render_to_string(
        "orders/email/status_update.txt", {"order": order, "site_domain": settings.SITE_DOMAIN}
    )
    send_mail(
        subject=f"Velore — статус замовлення {order.number} оновлено",
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
        fail_silently=True,
    )
