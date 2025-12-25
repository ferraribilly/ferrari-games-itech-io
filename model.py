from pymongo import MongoClient
from bson.objectid import ObjectId
import datetime
from dotenv import load_dotenv
import os
from datetime import datetime, timezone


# Carrega variáveis de ambiente
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")
USERS_COLLECTION_NAME = "users"
PAGAMENTOS_COLLECTION_NAME = "pagamentos"
PAGAMENTOS_APP_COLLECTION_NAME = "pagamentos_app"
ADMINS_COLLECTION_NAME = "admins"
COMPRAS_RF_COLLECTION_NAME = "compras_rf" 
COMPRAS_APP_COLLECTION_NAME = "compras_app"
SORTEIO_COLLECTION_NAME = "sorteio"
SAQUES_COLLECTION_NAME = "saques"
ASSINATURA_COLLECTION_NAME = "assinatura"





client = MongoClient(MONGO_URI)
db = client[DB_NAME]
#--------------------------------------------------------------------
# -PAGAMENTOS
#--------------------------------------------------------------------
pagamentos_collection = db[PAGAMENTOS_COLLECTION_NAME]

def criar_documento_pagamento(payment_id, status, valor, user_id, email_user, data_criacao=None):
    if data_criacao is None:
        
        data_criacao = datetime.now(timezone.utc)

    return {
        "_id": str(payment_id),
        "status": status,
        "valor": valor,
        "user_id": user_id,
        "email_user": email_user,
        "data_criacao": data_criacao,
        "data_atualizacao": None,
        "detalhes_webhook": None
    }


class PagamentoModel:
    def __init__(self):
        self.collection = pagamentos_collection

    def create_pagamento(self, data):
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    # existing method renamed/kept for backward compat
    def get_pagamento(self, pagamento_id):
        doc = self.collection.find_one({"_id": str(pagamento_id)})
        if doc:
            doc["_id"] = str(doc.get("_id"))
        return doc

    # alias esperado pela rota — evita AttributeError
    def get_pagamento_by_id(self, pagamento_id):
        return self.get_pagamento(pagamento_id)

    # garantir que todos os _id venham como string
    def get_all_pagamentos(self):
        docs = list(self.collection.find())
        for d in docs:
            d["_id"] = str(d.get("_id"))
        return docs

    def update_pagamento(self, pagamento_id, new_data):
        result = self.collection.update_one(
            {"_id": str(pagamento_id)},
            {"$set": new_data}
        )
        return result.modified_count

    def delete_pagamento(self, pagamento_id):
        result = self.collection.delete_one({"_id": str(pagamento_id)})
        return result.deleted_count

#======================================================
# COMPRAS RF
#======================================================
compras_rf_collection = db[COMPRAS_RF_COLLECTION_NAME]

class Compras_rfModel:
    def __init__(self):
        self.collection = compras_rf_collection

    def create_compras_rf(self, data):
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def get_compras_rf(self, compras_rf_id):
        doc = self.collection.find_one({"_id": str(compras_rf_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def get_compras_rf_by_id(self, compras_rf_id):
        return self.get_compras_rf(compras_rf_id)

    def get_all_compras_rf(self):
        docs = list(self.collection.find())
        for d in docs:
            d["_id"] = str(d["_id"])
        return docs

    def update_compras_rf(self, compras_rf_id, new_data):
        result = self.collection.update_one(
            {"_id": str(compras_rf_id)},
            {"$set": new_data}
        )
        return result.modified_count

    def delete_compras_rf(self, compras_rf_id):
        result = self.collection.delete_one(
            {"_id": str(compras_rf_id)}
        )
        return result.deleted_count

    def get_by_email(self, email):
           docs = list(self.collection.find({"email": email}))
           tickets = []
       
           for d in docs:
               tickets.extend(d.get("tickets", []))
       
           return tickets
#===================================================================================================
#SAQUES
#===================================================================================================
#======================================================
# 
#=====================================================
saques_collection = db[SAQUES_COLLECTION_NAME]
class SaquesModel:
    def __init__(self):
        self.collection = saques_collection

    def create_saques(self, data):
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def get_saques(self, saques_id):
        doc = self.collection.find_one({"_id": str(saques_id)})
        if doc:
            doc["_id"] = str(doc.get("_id"))
        return doc

    def get_saques_by_id(self, saques_id):
        return self.get_saques(saques_id)

    def get_all_saques(self):
        docs = list(self.collection.find())
        for d in docs:
            d["_id"] = str(d.get("_id"))
        return docs

    def update_saques(self, saques_id, new_data):
        result = self.collection.update_one(
            {"_id": str(saques_id)},
            {"$set": new_data}
        )
        return result.modified_count

    def delete_saques(self, saques_id):
        result = self.collection.delete_one({"_id": str(saques_id)})
        return result.deleted_count
        
#==================================================================================================
#==================================================================================================
#--------------------------------------------------------------------
# -PAGAMENTOS_APP
#--------------------------------------------------------------------
#-------------------------------------------------------------------------
# 
#-------------------------------------------------------------------------
compras_app_collection = db[COMPRAS_APP_COLLECTION_NAME]

def criar_documento_pagamento_app(payment_id, status, total, user_id, email_user, data_criacao=None):
    if data_criacao is None:
        
        data_criacao = datetime.now(timezone.utc)

    return {
        "_id": str(payment_id),
        "status": status,
        "total": total,
        "user_id": user_id,
        "email_user": email_user,
        "data_criacao": data_criacao,
        "data_atualizacao": None,
        "detalhes_webhook": None
    }
    



class Pagamento_appModel:
    def __init__(self):
        self.collection = db[PAGAMENTOS_APP_COLLECTION_NAME]        

    def create_pagamento_app(self, data):
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    # existing method renamed/kept for backward compat
    def get_pagamento_app(self, pagamento_app_id):
        doc = self.collection.find_one({"_id": str(pagamento_app_id)})
        if doc:
            doc["_id"] = str(doc.get("_id"))
        return doc

    # alias esperado pela rota — evita AttributeError
    def get_pagamento_app_by_id(self, pagamento_app_id):
        return self.get_pagamento_app(pagamento_app_id)

    # garantir que todos os _id venham como string
    def get_all_pagamentos_app(self):
        docs = list(self.collection.find())
        for d in docs:
            d["_id"] = str(d.get("_id"))
        return docs

    def update_pagamento_app(self, pagamento_app_id, new_data):
        result = self.collection.update_one(
            {"_id": str(pagamento_app_id)},
            {"$set": new_data}
        )
        return result.modified_count

    def delete_pagamento_app(self, pagamento_app_id):
        result = self.collection.delete_one({"_id": str(pagamento_app_id)})
        return result.deleted_count



        
#====================================================================================
# COMPRAS APP
#====================================================================================
class Compras_appModel:
    def __init__(self):
        self.collection = compras_app_collection

    def create_compras_app(self, data):
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def get_compras_app(self, compras_app_id):
        doc = self.collection.find_one({"_id": str(compras_app_id)})
        if doc:
            doc["_id"] = str(doc.get("_id"))
        return doc

    def get_compras_app_by_id(self, compras_app_id):
        return self.get_compras_app(compras_app_id)

    def get_all_compras_app(self):
        docs = list(self.collection.find())
        for d in docs:
            d["_id"] = str(d.get("_id"))
        return docs

    def update_compras_app(self, compras_app_id, new_data):
        result = self.collection.update_one(
            {"_id": str(compras_app_id)},
            {"$set": new_data}
        )
        return result.modified_count

    def delete_compras_app(self, compras_app_id):
        result = self.collection.delete_one({"_id": str(compras_app_id)})
        return result.deleted_count
#===================================================================================================
#===================================================================================================



#--------------------------------------------------------------------
# - SORTEIO
#--------------------------------------------------------------------
sorteio_collection = db[SORTEIO_COLLECTION_NAME]

class SorteioModel:
    def __init__(self):
        self.collection = sorteio_collection

    def create_sorteio(self, data):
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

    def get_sorteio(self, sorteio_id):
        try:
            oid = ObjectId(sorteio_id)
        except:
            return None

        doc = self.collection.find_one({"_id": oid})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def get_sorteio_by_id(self, sorteio_id):
        return self.get_sorteio(sorteio_id)

    def get_all_sorteio(self):
        docs = list(self.collection.find())
        for d in docs:
            d["_id"] = str(d["_id"])
        return docs

    def update_sorteio(self, sorteio_id, new_data):
        try:
            oid = ObjectId(sorteio_id)
        except:
            return 0

        result = self.collection.update_one(
            {"_id": oid},
            {"$set": new_data}
        )
        return result.modified_count

    def delete_sorteio(self, sorteio_id):
        try:
            oid = ObjectId(sorteio_id)
        except:
            return 0

        result = self.collection.delete_one({"_id": oid})
        return result.deleted_count
#===================================================================================================
#===================================================================================================



#------------------------------------------------------------
# -USERS
#------------------------------------------------------------
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






#======================================
# -Admins
#======================================

class AdminModel:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db[ADMINS_COLLECTION_NAME]

    def create_admin(self, admin_data):
        result = self.collection.insert_one(admin_data)
        return str(result.inserted_id)

    def get_all_admins(self):
        admins = list(self.collection.find())
        for admin in admins:
            admin['_id'] = str(admin['_id'])
        return admins

    def get_admin_by_id(self, admin_id):
        admin = self.collection.find_one({"_id": ObjectId(admin_id)})
        if admin:
            admin['_id'] = str(admin['_id'])
        return admin

    def get_admin_by_cpf(self, cpf):
        admin = self.collection.find_one({"cpf": cpf})
        if admin:
            admin['_id'] = str(admin['_id'])
        return admin

    def update_admin(self, admin_id, new_data):
        result = self.collection.update_one(
            {"_id": ObjectId(admin_id)},
            {"$set": new_data}
        )
        return result.modified_count

    def delete_admin(self, admin_id):
        result = self.collection.delete_one({"_id": ObjectId(admin_id)})
        return result.deleted_count



assinatura_collection = db[ASSINATURA_COLLECTION_NAME]

def criar_documento_assinatura(payment_id, status, valor, user_id, email_user, data_criacao=None):
    if data_criacao is None:
        
        data_criacao = datetime.now(timezone.utc)

    return {
        "_id": str(payment_id),
        "status": status,
        "valor": valor,
        "user_id": user_id,
        "email_user": email_user,
        "data_criacao": data_criacao,
        "data_atualizacao": None,
        "detalhes_webhook": None
    }


class AssinaturaModel:
    def __init__(self):
        self.collection = assinatura_collection

    def create_assinatura(self, data):
        result = self.collection.insert_one(data)
        return str(result.inserted_id)

   
    def get_assinatura(self, assinatura_id):
        doc = self.collection.find_one({"_id": str(assinatura_id)})
        if doc:
            doc["_id"] = str(doc.get("_id"))
        return doc

    
    def get_assinatura_by_id(self, assinatura_id):
        return self.get_assinatura(assinatura_id)

    # garantir que todos os _id venham como string
    def get_all_assinatura(self):
        docs = list(self.collection.find())
        for d in docs:
            d["_id"] = str(d.get("_id"))
        return docs

    def update_assinatura(self, assinatura_id, new_data):
        result = self.collection.update_one(
            {"_id": str(assinatura_id)},
            {"$set": new_data}
        )
        return result.modified_count

    def delete_assinatura(self, pagamento_id):
        result = self.collection.delete_one({"_id": str(assinatura_id)})
        return result.deleted_count
