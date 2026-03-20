from flask import Flask
import smtplib
import os
from email.message import EmailMessage

app = Flask(__name__)

def enviar_email():
    try:
        email_user = os.environ.get("EMAIL_USER")
        email_pass = os.environ.get("EMAIL_PASS")

        if not email_user or not email_pass:
            return "ERRO: Variáveis de ambiente não definidas"

        msg = EmailMessage()
        msg['Subject'] = "Assinatura Pro"
        msg['From'] = email_user
        msg['To'] = "corporacaoenigmagames@gmail.com"
        msg.set_content("Muito Obrigado por participar")

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(email_user, email_pass)
            server.send_message(msg)

        return "Email enviado com sucesso"

    except Exception as e:
        return f"ERRO REAL: {str(e)}"

@app.route("/")
def home():
    return enviar_email()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
