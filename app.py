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

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(email_user, email_pass)
        server.send_message(msg)

@app.route("/")
def home():
    enviar_email()
    return "Email enviado"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
