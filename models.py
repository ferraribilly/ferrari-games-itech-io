from pymongo import MongoClient, ASCENDING
from bson.objectid import ObjectId
import re
from dotenv import load_dotenv
import os
from datetime import datetime, timezone

# Carrega variáveis de ambiente
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")

if not MONGO_URI or not DB_NAME:
    raise ValueError("Variáveis de ambiente MONGO_URI ou DB_NAME não definidas.")

# Conexão com MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]

# Coleções
PAGAMENTOS_COLLECTION_NAME = "pagamentos"
users_collection = db["users"]


# Função para limpar CPF (remove pontos e traços)
def limpar_cpf(cpf: str) -> str:
    return re.sub(r"\D", "", cpf)

# Função para validar CPF simples (somente 11 dígitos)
def validar_cpf(cpf: str) -> bool:
    cpf = limpar_cpf(cpf)
    return bool(re.fullmatch(r"\d{11}", cpf))

# Criar usuário
def criar_usuario(nome: str, cpf: str, telefone: str) -> dict:
    cpf = limpar_cpf(cpf)

    if not nome.strip() or not validar_cpf(cpf) or not telefone.strip():
        raise ValueError("Dados inválidos para cadastro.")

    # Evita duplicado pelo CPF
    if users_collection.find_one({"cpf": cpf}):
        raise ValueError("CPF já cadastrado.")

    usuario = {
        "nome": nome.strip(),
        "cpf": cpf,
        "telefone": telefone.strip(),
        "criado_em": datetime.now(timezone.utc)
    }

    result = users_collection.insert_one(usuario)

    usuario["_id"] = str(result.inserted_id)
    return usuario




pagamentos_collection = db[PAGAMENTOS_COLLECTION_NAME]

def criar_documento_pagamento(payment_id, status, valor, usuario_id, telefone_user, data_criacao=None):
    if data_criacao is None:
        data_criacao = datetime.now(timezone.utc)

    return {
        "_id": str(payment_id),  # 👈 garante string
        "status": status,
        "valor": float(valor),   # 👈 garante número válido
        "usuario_id": str(usuario_id),
        "telefone_usuario": telefone_user,  # 👈 nome alinhado com rota
        "data_criacao": data_criacao,
        "data_atualizacao": None,
        "detalhes_webhook": None
    }


class PagamentoModel:
    def __init__(self):
        self.collection = pagamentos_collection

    def create_pagamento(self, data):
        try:
            # 👇 evita erro de duplicado (_id já existe)
            existente = self.collection.find_one({"_id": data["_id"]})
            if existente:
                return data["_id"]

            result = self.collection.insert_one(data)
            return str(result.inserted_id)

        except Exception as e:
            print("ERRO MODEL INSERT:", e)
            return None

    def get_pagamento(self, pagamento_id):
        doc = self.collection.find_one({"_id": str(pagamento_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
        return doc

    def get_pagamento_by_id(self, pagamento_id):
        return self.get_pagamento(pagamento_id)

    def get_all_pagamentos(self):
        docs = list(self.collection.find())
        for d in docs:
            d["_id"] = str(d["_id"])
        return docs

    def update_pagamento(self, pagamento_id, new_data):
        try:
            new_data["data_atualizacao"] = datetime.now(timezone.utc)

            result = self.collection.update_one(
                {"_id": str(pagamento_id)},
                {"$set": new_data}
            )
            return result.modified_count

        except Exception as e:
            print("ERRO UPDATE:", e)
            return 0

    def delete_pagamento(self, pagamento_id):
        try:
            result = self.collection.delete_one({"_id": str(pagamento_id)})
            return result.deleted_count

        except Exception as e:
            print("ERRO DELETE:", e)
            return 0
