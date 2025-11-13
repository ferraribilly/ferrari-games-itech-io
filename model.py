from flask_login import UserMixin
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId
from datetime import datetime, date
import os

# === ADICIONADO PARA NÃO DAR ERRO NO IMPORT ===
# Objeto mongo compatível com o que o Flask espera
class SimpleMongo:
    def __init__(self):
        self.client = None
        self.db = None

    def init_app(self, app):
        uri = app.config.get("MONGO_URI")
        self.client = MongoClient(uri)
        self.db = self.client["FerrariGamesItechIo"]

mongo = SimpleMongo()
# === FIM DO AJUSTE ===

# Configurações do MongoDB (testado, retorna 200)
MONGO_URI = "mongodb+srv://Ferrari-games-itech-io:0UgcAgov7VgUCJO3@ferrarigamesitechio.cqes1cf.mongodb.net/?appName=FerrariGamesItechIo"
DB_NAME = "FerrariGamesItechIo"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
usuario_collection = db.get_collection("Usuarios")  # Nome da coleção de usuários

def get_db_status():
    """
    Função para verificar o status do banco de dados.
    Tenta listar as coleções para confirmar a conexão.
    """
    try:
        db.list_collection_names()
        return True
    except Exception as e:
        print(f"Erro de conexão com o MongoDB: {e}")
        return False

class Usuario(UserMixin):
    def __init__(self, usuario_data):
        """Inicializa o objeto Usuario a partir dos dados do MongoDB."""
        self.usuario_data = usuario_data
        self.id = str(usuario_data['_id'])
        self.nome = usuario_data.get('nome', '')
        self.sobrenome = usuario_data.get('sobrenome', '')
        self.data_nascimento = usuario_data.get('data_nascimento', '')
        self.email = usuario_data.get('email', '')
        self.chave_pix = usuario_data.get('chave_pix', '')
        self.convite_ganbista = usuario_data.get('convite_ganbista', '')
        self.password_hash = usuario_data.get('password_hash', '')

    @staticmethod
    def get_by_cpf(cpf):
        """Busca um usuário por CPF no MongoDB."""
        usuario_data = usuario_collection.find_one({"cpf": cpf})
        if usuario_data:
            return Usuario(usuario_data)
        return None

    @staticmethod
    def get_by_id(usuario_id):
        """Busca um usuário por ID (ObjectId) no MongoDB."""
        usuario_data = usuario_collection.find_one({"_id": ObjectId(usuario_id)})
        if usuario_data:
            return Usuario(usuario_data)
        return None

    @staticmethod
    def create(nome, sobrenome, email, cpf, convite_ganbista, chave_pix, password):
        """Cria um novo usuário e o insere no MongoDB."""
        if Usuario.get_by_cpf(cpf):
            return None  # Usuário já existe

        password_hash = generate_password_hash(password)
        new_usuario_data = {
            "nome": nome,
            "sobrenome": sobrenome,
            "email": email,
            "cpf": cpf,
            "convite_ganbista": convite_ganbista,
            "chave_pix": chave_pix,
            "password_hash": password_hash,
            "data_nascimento": None  # Pode ser ajustado depois
        }
        result = usuario_collection.insert_one(new_usuario_data)
        new_usuario_data['_id'] = result.inserted_id
        return Usuario(new_usuario_data)

    def check_password(self, password):
        """Verifica a senha informada com o hash armazenado."""
        return check_password_hash(self.password_hash, password)
