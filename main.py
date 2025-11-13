# main.py
from flask import Flask
from model import mongo
from view import main_bp
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
load_dotenv()  # carrega .env em os.environ — NÃO usar em produção que já tem variáveis
def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "chave_super_secreta_troque_isto")

    # MongoDB config
    app.config["MONGO_URI"] = os.environ.get("MONGO_URI", "mongodb+srv://<username>:<password>@<cluster-url>/<db-name>?retryWrites=true&w=majority")

    mongo.init_app(app)
    app.register_blueprint(main_bp)
    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
