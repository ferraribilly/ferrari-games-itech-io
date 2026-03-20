from flask import Flask
import smtplib
import os
from email.message import EmailMessage

app = Flask(__name__)

def enviar_email():
    email_user = os.environ.get("EMAIL_USER")
    email_pass = os.environ.get("EMAIL_PASS")

    msg = EmailMessage()
    msg['Subject'] = "Assinatura Pro"
    msg['From'] = email_user
    msg['To'] = "corporacaoenigmagames@gmail.com"
    msg.set_content("Muito Obrigado por participar")

    # SSL DIRETO (porta 465)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(email_user, email_pass)
        server.send_message(msg)

@app.route("/")
def home():
    enviar_email()
    return "Email enviado"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Render usa isso
    app.run(host="0.0.0.0", port=port)
