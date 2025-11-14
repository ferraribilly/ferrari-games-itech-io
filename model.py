from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime

# Configurações de conexão (ajuste conforme necessário)
MONGO_URI = "mongodb+srv://Ferrari-games-itech-io:0UgcAgov7VgUCJO3@ferrarigamesitechio.cqes1cf.mongodb.net/?appName=FerrariGamesItechIo"
DB_NAME = "FerrariGamesItechIo"
USERS_COLLECTION_NAME = "users"
PAGAMENTOS_COLLECTION_NAME = "pagamentos"

# Conexão com o MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
pagamentos_collection = db[PAGAMENTOS_COLLECTION_NAME]

# Função para criar documento de pagamento
def criar_documento_pagamento(payment_id, status, valor, user_id, email_user, data_criacao=None):
    """
    Cria um dicionário que representa um documento de pagamento para o MongoDB.
    """
    if data_criacao is None:
        data_criacao = datetime.datetime.utcnow()

    return {
        "_id": payment_id,  # Usaremos o ID do Mercado Pago como o ID do documento
        "status": status,
        "valor": valor,
        "user_id": user_id,
        "email_user": email_user,
        "data_criacao": data_criacao,
        "data_atualizacao": None,
        "detalhes_webhook": None
    }

#============≈=========≈============
# -Collection "Users"
#===================================
class UsuarioModel:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db[USERS_COLLECTION_NAME]

    def create_user(self, user_data):
        """Insere um novo documento (usuário) na coleção."""
        result = self.collection.insert_one(user_data)
        return str(result.inserted_id)

    def get_all_users(self):
        """Recupera todos os documentos (usuários) da coleção."""
        users = list(self.collection.find())
        for user in users:
            user['_id'] = str(user['_id'])
        return users

    def get_user_by_id(self, user_id):
        """Recupera um único documento (usuário) por ID."""
        user = self.collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user['_id'] = str(user['_id'])
        return user

    def get_user_by_cpf(self, cpf):
        """Busca por CPF (para rota de login)."""
        user = self.collection.find_one({"cpf": cpf})
        if user:
            user['_id'] = str(user['_id'])
        return user

    def update_user(self, user_id, new_data):
        """Atualiza um documento (usuário) existente."""
        result = self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": new_data}
        )
        return result.modified_count

    def delete_user(self, user_id):
        """Exclui um documento (usuário) existente."""
        result = self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count
