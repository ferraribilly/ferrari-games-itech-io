from flask import Flask
from flask_login import LoginManager
from model import mongo, Usuario  # Alterado de User para Usuario
# Importa as funções de view para conectar as rotas
from view import register, login, painel, logout
from view import main_bp
import os
from dotenv import load_dotenv

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config["MONGO_URI"] = "mongodb+srv://Ferrari-games-itech-io:0UgcAgov7VgUCJO3@ferrarigamesitechio.cqes1cf.mongodb.net/?appName=FerrariGamesItechIo"
    app.secret_key = os.environ.get("SECRET_KEY", "chave_super_secreta_troque_isto")

    mongo.init_app(app)
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'  # Define para onde redirecionar se o login for necessário

    @login_manager.user_loader
    def load_usuario(usuario_id):
        return Usuario.get_by_id(usuario_id)  # Alterado de User para Usuario

    # Conecta as rotas (views) ao app
    app.add_url_rule('/register', 'register', register, methods=['GET', 'POST'])
    app.add_url_rule('/login', 'login', login, methods=['GET', 'POST'])
    app.add_url_rule('/painel', 'painel', painel)
    app.add_url_rule('/logout', 'logout', logout)
    app.add_url_rule('/', 'index', login)  # Redireciona a página inicial para o login

    app.register_blueprint(main_bp)
    return app

if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
