# model.py
from pymongo import MongoClient
from bson.objectid import ObjectId

# Configurações de conexão (ajuste conforme necessário)
MONGO_URI = "mongodb+srv://Ferrari-games-itech-io:0UgcAgov7VgUCJO3@ferrarigamesitechio.cqes1cf.mongodb.net/?appName=FerrariGamesItechIo"
DB_NAME = "FerrariGamesItechIo"
COLLECTION_NAME = "users"/

class UsuarioModel:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db[COLLECTION_NAME]

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

    # ============================================================
    # Busca por CPF (para rota de login)
    # ============================================================
    def get_user_by_cpf(self, cpf):
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
