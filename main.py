# main.py
from flask import Flask, request, jsonify, abort, render_template, redirect, url_for
import mercadopago
from datetime import datetime
#from model import UsuarioModel
from model import UsuarioModel, pagamentos_collection, criar_documento_pagamento
from bson.errors import InvalidId
import os
import re
import json
from model import pagamentos_collection, criar_documento_pagamento

app = Flask(__name__)
#==============================================
# Configurar o SDK do Mercado Pago
# Use variáveis de ambiente para suas credenciais
#==============================================
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "SEU_ACCESS_TOKEN")
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)
#======================================
# -Collections model.py
#======================================
user_model = UsuarioModel()

# ====================================
# -Criar usuarios
# ====================================
@app.route('/users', methods=['POST'])
def create_user():
    """Rota para criar um novo usuário."""
    data = request.get_json()
    if not data or \
       'nome' not in data or \
       'email' not in data or \
       'cpf' not in data or \
       'data_nascimento' not in data or \
       'chave_pix' not in data or \
       'convite_ganbista' not in data:
        return jsonify({"error": "Dados inválidos fornecidos."}), 400
    
    user_id = user_model.create_user(data)
    return jsonify({"message": "Usuário criado com sucesso", "id": user_id}), 201
# ====================================
# -Listar usuarios
# ====================================
@app.route('/users', methods=['GET'])
def get_users():
    """Rota para listar todos os usuários."""
    users = user_model.get_all_users()
    return jsonify(users), 200
# ====================================
# -Obter um unico usuario
# ====================================
@app.route('/users/<string:user_id>', methods=['GET'])
def get_user(user_id):
    """Rota para obter um usuário específico por ID."""
    try:
        user = user_model.get_user_by_id(user_id)
        if user:
            return jsonify(user), 200
        return jsonify({"error": "Usuário não encontrado."}), 404
    except InvalidId:
        return jsonify({"error": "ID de usuário inválido."}), 400
# ====================================
# -Atualizar um usuario
# ====================================
@app.route('/users/<string:user_id>', methods=['PUT'])
def update_user_route(user_id):
    """Rota para atualizar um usuário existente."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Nenhum dado fornecido para atualização."}), 400

    try:
        modified_count = user_model.update_user(user_id, data)
        if modified_count > 0:
            return jsonify({"message": "Usuário atualizado com sucesso."}), 200
        return jsonify({"error": "Usuário não encontrado ou nenhum dado alterado."}), 404
    except InvalidId:
        return jsonify({"error": "ID de usuário inválido."}), 400
# ====================================
# -Excluir um usuario
# ====================================
@app.route('/users/<string:user_id>', methods=['DELETE'])
def delete_user_route(user_id):
    """Rota para excluir um usuário."""
    try:
        deleted_count = user_model.delete_user(user_id)
        if deleted_count > 0:
            return jsonify({"message": "Usuário excluído com sucesso."}), 200
        return jsonify({"error": "Usuário não encontrado."}), 404
    except InvalidId:
        return jsonify({"error": "ID de usuário inválido."}), 400

# ============================
# ROTA LOGIN VIA CPF (NORMALIZA CPFs PARA COMPARAÇÃO)
# ============================
def only_digits(s):
    return re.sub(r'\D', '', s or "")

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or 'cpf' not in data:
        return jsonify({"error": "CPF obrigatório."}), 400

    input_cpf = only_digits(data["cpf"])

    # procurar usuário por CPF normalizado
    users = user_model.get_all_users()
    for user in users:
        user_cpf = only_digits(user.get("cpf", ""))
        if user_cpf == input_cpf and user.get("_id"):
            user_id = str(user["_id"])
            return jsonify({
                "redirect": f"/loading/users/{user_id}"
            }), 200

    return jsonify({"error": "CPF não encontrado."}), 404

# ====================================
# -Criar Pagamentos 
# ================================
# ====================================
# -Criar Pagamentos
# ====================================
@app.route("/criar-pagamento/users/<string:user_id>", methods=["POST"])
def criar_pagamento(user_id):
    # Lógica para criar uma preferência de pagamento no Mercado Pago
    data = request.get_json()
    item_titulo = data.get("titulo")
    item_valor = data.get("valor")
    email_user = data.get("email")

    if not item_titulo or not item_valor or not email_user:
        return jsonify({"erro": "Dados insuficientes"}), 400

    preference_data = {
        "items": [
            {
                "title": item_titulo,
                "quantity": 1,
                "unit_price": float(item_valor),
            }
        ],
        "payer": {"email": email_user},
        "back_urls": {
            "success": "https://ferrari-games-itech-io.onrender.com/feedback/success",
            "failure": "https://ferrari-games-itech-io.onrender.com/feedback/failure",
            "pending": "https://ferrari-games-itech-io.onrender.com/feedback/pending",
        },
        "notification_url": "https://ferrari-games-itech-io.onrender.com/notificacoes",
        "auto_return": "approved",
    }

    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]

    # Salvar a preferência inicial no MongoDB
    pagamento_doc = criar_documento_pagamento(
        payment_id=preference["id"],
        status="pending",
        valor=float(item_valor),
        user_id=user_id,
        email_user=email_user
    )
    pagamentos_collection.insert_one(pagamento_doc)

    return jsonify({"id_preferencia": preference["id"], "link_pagamento": preference["init_point"]})





@app.route("/notificacoes", methods=["POST"])
def webhook_mp():

    # Endpoint para o Mercado Pago enviar notificações (webhooks)
    data = request.get_json()
    
    # Valide se a notificação é real (veja a documentação do MP sobre assinaturas)
    # Por simplicidade, aqui apenas processamos o ID do pagamento
    topic = data.get("topic", data.get("type"))
    
    if topic == "payment":
        payment_id = data.get("data", {}).get("id")
        if payment_id:
            # Consultar a API do MP para obter detalhes do pagamento
            payment_info = sdk.payment().get(payment_id)
            if payment_info["status"] == 200:
                payment_data = payment_info["response"]
                status = payment_data.get("status")
                
                # Atualizar o documento no MongoDB
                # Note: O payment_id do webhook é diferente do preference_id inicial. 
                # Você precisa ajustar sua lógica para mapear corretamente. 
                # Um jeito fácil é usar o order.id ou external_reference na preferência.
                # Para este exemplo simplificado, vamos apenas registrar o webhook:
                
                pagamentos_collection.update_one(
                    {"_id": payment_id}, # Isso só funcionará se você usar o payment_id real como _id
                    {"$set": {
                        "status": status,
                        "data_atualizacao": datetime.utcnow(),
                        "detalhes_webhook": payment_data
                    }},
                    upsert=True # Cria o documento se não existir (caso a notificação chegue antes do insert inicial)
                )
                print(f"Pagamento {payment_id} atualizado para o status: {status}")
            
    return jsonify({"status": "ok"}), 200
# ============================
# -Rotas do app templates
# ============================

#==============================================≈==
# -Pagina inicial registro usuarios
#==============================================≈==
@app.route('/')
def criar_user():
    return render_template('jogo_bixo/registro.html')
#==============================================≈=====
# -Pagina Carregamento....loading
#==============================================≈=====
@app.route('/loading/users/<string:user_id>')
def loading(user_id):
    return render_template('jogo_bixo/carregando.html')
#==============================================≈=======
# -Painel de navegação
#==============================================≈=======
@app.route('/painel/users/<string:user_id>')
def painel(user_id):
    return render_template('jogo_bixo/painel_game.html')
#==============================================≈===
# -Compras no app
#==============================================≈===
@app.route('/compras/app/users/<string:user_id>')
def compras(user_id):
    return render_template('jogo_bixo/pagamentos/depositos.html')
#==============================================≈=================
# -Pagamento Pendente
#==============================================≈=================
@app.route('/pending')
def pending(user_id):
    return render_template('jogo_bixo/pagamentos/pending.html')
#==============================================≈===============
# -Pagamento Falhou 
#==============================================≈===============
@app.route('/failure')
def failure(user_id):
    return render_template('jogo_bixo/pagamentos/failure.html')

#======================================================
# -Painel dos Jogos do app
@app.route('/jogo_bicho')
def jogo_bicho():
    return render_template('jogo_bixo/jogo_bicho.html')

@app.route('/slot')    
def slot_jogo_bicho():
    return render_template('jogo_bixo/slotmachine.html')
    
@app.route('/bingo')
def bingo():
    return render_template('bingo/game.html')

@app.route('/painel/rifa_da_sorte/users/<string:user_id>')    
def rifa(user_id):
    return render_template('rifa/rifa.html')
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
