from flask import Flask
from model import db
from view import main_bp
import os

def create_app():
    app = Flask(__name__)
    

    # Chave secreta para sessão
    app.secret_key = os.environ.get("SECRET_KEY", "chave_super_secreta_troque_isto")

    # Configuração do banco de dados SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(
        os.path.abspath(os.path.dirname(__file__)), 'app.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Inicializa o db com o app
    db.init_app(app)

    # Registra o blueprint das rotas
    app.register_blueprint(main_bp)

    return app


if __name__ == '__main__':
    import os
    app = create_app()

    # Cria as tabelas no banco de dados, se não existirem
    with app.app_context():
        db.create_all()

    # Porta e host para o Render
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
