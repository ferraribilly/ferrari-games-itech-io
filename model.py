# model.py
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, date
import os






# model.py

from pymongo import MongoClient

# Configurações do MongoDB
MONGO_URI = "mongodb+srv://Ferrari-games-itech-io:0UgcAgov7VgUCJO3@ferrarigamesitechio.cqes1cf.mongodb.net/?appName=FerrariGamesItechIo" # Substitua pela sua URI de conexão, se necessário
DB_NAME = "FerrariGamesItechIo" # Substitua pelo nome do seu banco de dados

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def get_db_status():
    """
    Função para verificar o status do banco de dados.
    Tenta listar as coleções para confirmar a conexão.
    """
    try:
        # Tenta listar as coleções para verificar se a conexão está ativa
        db.list_collection_names()
        return True
    except Exception as e:
        print(f"Erro de conexão com o MongoDB: {e}")
        return False










# Conexão MongoDB
#mongo_uri = os.environ.get(
#    "MONGO_URI",
#    "mongodb+srv://Ferrari-games-itech-io:0UgcAgov7VgUCJO3@ferrarigamesitechio.cqes1cf.mongodb.net/?appName=FerrariGamesItechIo"
#)
#client = MongoClient(mongo_uri)

# Banco de dados e coleção
db_name = "FerrariGamesItechIo"
db = client[db_name]  # Corrigido: db_name como string
usuarios_collection = db["usuarios"]  # cria automaticamente se não existir

class Usuario:
    def __init__(self, nome, sobrenome, cpf, data_nascimento, email, chave_pix, convite_ganbista, senha):
        self.nome = nome
        self.sobrenome = sobrenome
        self.cpf = cpf
        self.data_nascimento = data_nascimento
        self.email = email
        self.chave_pix = chave_pix
        self.convite_ganbista = convite_ganbista
        self.senha = senha  # idealmente hash

    def save(self):
        data = {
            "nome": self.nome,
            "sobrenome": self.sobrenome,
            "cpf": self.cpf,
            "data_nascimento": self.data_nascimento.strftime("%Y-%m-%d") if isinstance(self.data_nascimento, date) else self.data_nascimento,
            "email": self.email,
            "chave_pix": self.chave_pix,
            "convite_ganbista": self.convite_ganbista,
            "senha": self.senha
        }
        result = usuarios_collection.insert_one(data)
        return result.inserted_id

    @staticmethod
    def find_all():
        return list(usuarios_collection.find())

    @staticmethod
    def find_by_cpf(cpf):
        return usuarios_collection.find_one({"cpf": cpf})

    @staticmethod
    def update_user(_id, data):
        return usuarios_collection.update_one({"_id": ObjectId(_id)}, {"$set": data})
