import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()
def enviar_email():
    # 1º) pegue as variavel de ambiente
    email_user = os.environ.get("EMAIL_USER")
    email_pass = os.environ.get("EMAIL_PASS")

    # 2º) Monte a extrutura do email
    msg = EmailMessage()
    msg['Subject'] = "Assinatura Pro"
    msg['From'] = email_user
    msg['To'] = "corporacaoenigmagames@gmail.com"
    msg.set_content("Muito Obrigado por participar")

    # 3º) Conect uando STARTTLS na porta 587
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_user, email_pass)
            server.send_message(msg)
            print("Email enviado com sucesso")
    except Exception as e:
        print(f"Erro ao enviar: {e}")

enviar_email()        


