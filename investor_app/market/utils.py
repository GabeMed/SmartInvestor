from django.core.mail import send_mail
from django.conf import settings

def email_alert(email, tipo, asset):
    """Sends a buy ("compra") or sell ("venda") suggestion for a monitored asset."""

    assunto = f"Sugestão de {tipo}: {asset.code.code} <Smart Investor>"
    mensagem = (
        f"{asset.code.code} está cotado a R$ {asset.price}, "
        f"fora da faixa definida (R$ {asset.lower_limit} a R$ {asset.upper_limit}). "
        f"Pode ser um bom momento para {tipo}; entre em nossa plataforma para conferir."
    )

    send_mail(
        subject=assunto,
        message=mensagem,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
