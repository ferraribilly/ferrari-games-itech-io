from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    sobrenome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    chave_pix = db.Column(db.String(100), nullable=False)
    convite_ganbista = db.Column(db.String(255), nullable=False)
    senha = db.Column(db.String(255), nullable=False) # Armazenar hash da senha

    def __repr__(self):
        return f'<Usuario {self.nome}>'
