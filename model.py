# model.py
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os

# Conexão MongoDB
mongo_uri = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://Ferrari-games-itech-io:0UgcAgov7VgUCJO3@ferrarigamesitechio.cqes1cf.mongodb.net/FerrariGamesItechIo?appName=FerrariGamesItechIo"
)
client = MongoClient(mongo_uri)

# Especifica o banco de dados padrão
db_name = "FerrariGamesItechIo"
db = client[db_name]

class Usuario:
    def __init__(self, nome, sobrenome, cpf, data_nascimento, email, chave_pix, convite_ganbista, senha):
        self.nome = nome
        self.sobrenome = sobrenome
        self.cpf = cpf
        self.data_nascimento = data_nascimento
        self.email = email
        self.chave_pix = chave_pix
        self.convite_ganbista = convite_ganbista
        self.senha = senha  # hash idealmente

    @staticmethod
    def collection():
        return db.usuarios

    def save(self):
        data = {
            "nome": self.nome,
            "sobrenome": self.sobrenome,
            "cpf": self.cpf,
            "data_nascimento": self.data_nascimento,
            "email": self.email,
            "chave_pix": self.chave_pix,
            "convite_ganbista": self.convite_ganbista,
            "senha": self.senha
        }
        result = self.collection().insert_one(data)
        return result.inserted_id

    @staticmethod
    def find_all():
        return list(Usuario.collection().find())

    @staticmethod
    def find_by_cpf(cpf):
        return Usuario.collection().find_one({"cpf": cpf})

    @staticmethod
    def update_user(_id, data):
        return Usuario.collection().update_one({"_id": ObjectId(_id)}, {"$set": data})
