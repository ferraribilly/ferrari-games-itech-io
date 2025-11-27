from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
from dotenv import load_dotenv
import os

# Carrega variáveis de ambiente
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
USERS_COLLECTION_NAME = "users"
PAGAMENTOS_COLLECTION_NAME = "pagamentos"
BALANCE_COLLECTION_NAME = "balance"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

pagamentos_collection = db[PAGAMENTOS_COLLECTION_NAME]
balance_collection = db[BALANCE_COLLECTION_NAME]



def criar_documento_pagamento(payment_id, status, valor, user_id, email_user, data_criacao=None):
    if data_criacao is None:
        data_criacao = datetime.datetime.utcnow()

    return {
        "_id": payment_id,
        "status": status,
        "valor": valor,
        "user_id": user_id,
        "email_user": email_user,
        "data_criacao": data_criacao,
        "data_atualizacao": None,
        "detalhes_webhook": None
    }


def criar_balance(user_id, balance):
    user_id = str(user_id)
    existente = balance_collection.find_one({"user_id": user_id})
    if existente:
        balance_collection.update_one(
            {"user_id": user_id},
            {"$inc": {"balance": float(balance)}}
        )
    else:
        balance_collection.insert_one({
            "user_id": user_id,
            "balance": float(balance),
            "data_criacao": datetime.datetime.utcnow()
        })


class BalanceModel:
    def __init__(self):
        self.collection = balance_collection

    def get_balance_by_user(self, user_id):
        user_id = str(user_id)
        bal = self.collection.find_one({"user_id": user_id})
        if bal:
            bal["_id"] = str(bal["_id"])
        return bal

    def get_all_balances(self):
        list_bal = list(self.collection.find())
        for b in list_bal:
            b["_id"] = str(b["_id"])
        return list_bal

    def update_balance(self, user_id, new_data):
        user_id = str(user_id)
        result = self.collection.update_one(
            {"user_id": user_id},
            {"$set": new_data},
            upsert=True
        )
        # Se inserir novo documento, upserted_id será != None. Retornamos 1 para indicar sucesso.
        if getattr(result, "upserted_id", None):
            return 1
        return result.modified_count

    def delete_balance(self, user_id):
        user_id = str(user_id)
        result = self.collection.delete_one({"user_id": user_id})
        return result.deleted_count


class PagamentoModel:
    def __init__(self):
        self.collection = pagamentos_collection

    def create_pagamento(self, data):
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def get_pagamento(self, pagamento_id):
        return self.collection.find_one({"_id": pagamento_id})

    def get_all_pagamentos(self):
        return list(self.collection.find())

    def update_pagamento(self, pagamento_id, new_data):
        result = self.collection.update_one(
            {"_id": pagamento_id},
            {"$set": new_data}
        )
        return result.modified_count

    def delete_pagamento(self, pagamento_id):
        result = self.collection.delete_one({"_id": pagamento_id})
        return result.deleted_count


class UsuarioModel:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db[USERS_COLLECTION_NAME]

    def create_user(self, user_data):
        result = self.collection.insert_one(user_data)
        return str(result.inserted_id)

    def get_all_users(self):
        users = list(self.collection.find())
        for user in users:
            user['_id'] = str(user['_id'])
        return users

    def get_user_by_id(self, user_id):
        user = self.collection.find_one({"_id": ObjectId(user_id)})
        if user:
            user['_id'] = str(user['_id'])
        return user

    def get_user_by_cpf(self, cpf):
        user = self.collection.find_one({"cpf": cpf})
        if user:
            user['_id'] = str(user['_id'])
        return user

    def update_user(self, user_id, new_data):
        result = self.collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": new_data}
        )
        return result.modified_count

    def delete_user(self, user_id):
        result = self.collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count
