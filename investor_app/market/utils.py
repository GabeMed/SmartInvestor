from django.core.mail import send_mail
from django.conf import settings

def email_alert(email, tipo):
    
    assunto = f"Sugestão de {tipo} <Smart Investor>"
    mensagem = (f"Alguma de suas ações atingiu um bom preço para {tipo} entre em nossa plataforma para conferir.")

    send_mail(
        subject=assunto,
        message=mensagem,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )
