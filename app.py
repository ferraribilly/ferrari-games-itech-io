from flask import Flask, request, jsonify, abort, render_template, redirect, url_for
from flask_socketio import SocketIO, join_room, emit
import requests
import mercadopago
from io import BytesIO
import base64
import qrcode
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from model import UsuarioModel, AdminModel, Compras_appModel, SaquesModel, Compras_rfModel, SorteioModel, Pagamento_appModel, PagamentoModel, compras_app_collection, criar_documento_pagamento_app, pagamentos_collection, criar_documento_pagamento
from bson.errors import InvalidId
import os
import re
import json
from bson.objectid import ObjectId
from flask_cors import CORS
import random
import cloudinary
import cloudinary.uploader
import tempfile
from dotenv import load_dotenv


load_dotenv()
app = Flask(__name__)
# app = Flask(__name__, static_folder="static", template_folder="templates")
socketio = SocketIO(app, cors_allowed_origins="*") 
app.secret_key = 'sua_chave_secreta' 
user_model = UsuarioModel()
saques_model = SaquesModel()
pagamento_model = PagamentoModel()      
pagamento_app_model = Pagamento_appModel()
admin_model = AdminModel()
compras_rf_model = Compras_rfModel()
compras_app_model = Compras_appModel()
sorteio_model = SorteioModel()
os.makedirs('static/images', exist_ok=True)
os.makedirs('static/upload', exist_ok=True)
CORS(app)


@app.route('/msg/<string:user_id>')
def msg(user_id):
    return render_template("msg.html",user_id=user_id)

#==========================================================================================
# CRIAR REGISTRO DOS USER 
#==========================================================================================

@app.route("/users", methods=["POST"])
def register_user():
    data = request.get_json()
    required = ["nome","sobrenome", "cidade", "cpf","data_nascimento","email","senha"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Campo obrigatório: {field}"}), 400
    cpf_digits = re.sub(r"\D", "", data["cpf"])
    exists = user_model.get_user_by_cpf(cpf_digits)
    if exists:
        return jsonify({"error": "CPF já registrado"}), 409

    new_user = {
        "nome": data["nome"],
        "sobrenome": data["sobrenome"],
        "cidade": data.get("cidade",""),
        "cpf": cpf_digits,
        "data_nascimento": data["data_nascimento"],
        "email": data["email"],
        "convite_ganbista": data.get("convite_ganbista",""),
        "chave_pix": data.get("chave_pix",""),
        "senha": data["senha"],
        "balance": 0,  
        "created_at": datetime.now()
    }
    user_id = user_model.create_user(new_user)
    return jsonify({"id": user_id}), 201


#==================================================================
# GET USER
#==================================================================
@app.route("/users/<string:user_id>", methods=["GET"])
def get_user(user_id):
    user = user_model.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404
    user["_id"] = str(user["_id"])
    return jsonify(user), 200


#===========================================================
# PUT USER
#===========================================================
@app.route("/users/<string:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json()
    updated = user_model.update_user(user_id, data)
    if not updated:
        return jsonify({"error": "Usuário não encontrado"}), 404
    return jsonify({"status": "atualizado"}), 200


#=========================================================
# DELETE USER
#=========================================================
@app.route("/users/<string:user_id>", methods=["DELETE"])
def delete_user(user_id):
    deleted = user_model.delete_user(user_id)
    if not deleted:
        return jsonify({"error": "Usuário não encontrado"}), 404
    return jsonify({"status": "removido"}), 200


#========================================
# LOGIN CPF
#========================================
#========================================
# -LOGIN E REGISTRO DOS USERS
#========================================

@app.route("/")
def index():
    return render_template("index.html")
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    cpf = data.get("cpf", "")

    cpf_digits = re.sub(r"\D", "", cpf)
    user = user_model.get_user_by_cpf(cpf_digits)

    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    # Login sem senha, igual seu frontend quer
    return jsonify({
        "redirect": f"/acesso/users/painel/{user['_id']}"
    })


#============================================================================================
#============================================================================================


#MAQUINA TEMPO REAL COM SOCKET
#=========================================================
# -LEVEL MAQUINA 3X3 ADCIONAR SOCKET POIS SERA TEMPO REAL.
#=========================================================
LEVEL = 1
#SERA CONTROLADO PELO CPF OU USER_ID QUER TER EXEMPLO: CPF: 459.772.778-73 lEVEL=1 ASSIM POR DIANTE VAI TER 5 USERS AQUI OK 
#SERA CONTROLADO COM A QUANTIDADE DE USERS CONECTADOS E TOTAL SOMADO DO BALANCE DE TODOS SE TIVER 3 USERS CADA COM 5.00 DE BALANCE 2 PERDERA 1 1 VAI GANHAR 5.00 SE FICAR JOGANDO APOS OS 2 USER TER BALANCE 0 ELE COMECA PERDER ATE PARA  OK
SYMBOL_NAMES = [
    '1','2','3',
    '4','5','6',
    '7','8','9',
    '10','11','12',
    '13','14','15',
]

SYMBOL_VALUES = {
    "1": 0.05, 
    "2": 0.10, 
    "3": 0.10, 
    "4": 0.10, 
    "5": 0.35, 
    "6": 0.15, 
    "7": 0.50, 
    "8": 0.75,
    "9": 1.00,
    "10": 1.25,
    "11": 1.75,
    "12": 2.25,
    "13": 3.75,
    "14": 4.50,
    "15": 5.00,
}

class Machine:
    def __init__(self, balance=1000.0):
        self.balance = float(balance)

machine = Machine()

def random_symbol():
    return random.choice(SYMBOL_NAMES)

def generate_grid():
    grid = [[random_symbol() for r in range(3)] for c in range(3)]

    if LEVEL == 1:
        for c in range(3):
            sym = random_symbol()
            for r in range(3):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]

        for r in range(3):
            sym = random_symbol()
            for c in range(3):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]

        sym = random_symbol()
        for i in range(3):
            grid[i][i] = sym if random.randint(0,1) else grid[i][i]

        sym = random_symbol()
        for i in range(3):
            grid[i][2-i] = sym if random.randint(0,1) else grid[i][2-i]

        sym = random_symbol()
        for c,r in [(0,0),(2,2),(0,2),(2,0),(1,1)]:
            grid[c][r] = sym if random.randint(0,1) else grid[c][r]

        sym = random_symbol()
        for c,r in [(0,0),(2,2),(2,0),(0,2)]:
            grid[c][r] = sym if random.randint(0,1) else grid[c][r]

        sym = random_symbol()
        for c,r in [(0,0),(1,0),(2,0),(0,2),(1,2),(2,2),(0,1),(2,1)]:
            grid[c][r] = sym if random.randint(0,1) else grid[c][r]

        sym = random_symbol()
        for c in range(3):
            for r in range(3):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]

    elif LEVEL == 2:
        for c in range(3):
            sym = random_symbol()
            for r in range(3):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]
        for r in range(3):
            sym = random_symbol()
            for c in range(3):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]

    elif LEVEL == 3:
        for c in range(3):
            sym = random_symbol()
            for r in range(3):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]

    return grid

def check_wins(grid):
    wins = []

    def addWin(type_, positions, multiplier):
        wins.append({
            "type": type_,
            "positions": positions,
            "payout": multiplier
        })

    for r in range(3):
        if all(grid[c][r] == grid[0][r] for c in range(3)):
            addWin("horizontal", [(c,r) for c in range(3)], 5)

    for c in range(3):
        if all(grid[c][r] == grid[c][0] for r in range(3)):
            addWin("vertical", [(c,r) for r in range(3)], 8)

    if all(grid[i][i] == grid[0][0] for i in range(3)):
        addWin("diagonal_principal", [(i,i) for i in range(3)], 12)

    if all(grid[i][2-i] == grid[0][2] for i in range(3)):
        addWin("diagonal_invertida", [(i,2-i) for i in range(3)], 12)

    if (
        grid[0][0] == grid[2][2] ==
        grid[0][2] == grid[2][0] ==
        grid[1][1]
    ):
        addWin("cruzado_x", [(0,0),(2,2),(0,2),(2,0),(1,1)], 20)

    if (
        grid[0][0] == grid[2][2] ==
        grid[2][0] == grid[0][2]
    ):
        addWin("janela", [(0,0),(2,2),(2,0),(0,2)], 15)

    borda_pos = [(0,0),(1,0),(2,0),(0,2),(1,2),(2,2),(0,1),(2,1)]
    borda = [grid[c][r] for c,r in borda_pos]
    if all(s == borda[0] for s in borda):
        addWin("janelao", borda_pos, 30)

    full_pos = [(c,r) for c in range(3) for r in range(3)]
    flat = [grid[c][r] for c,r in full_pos]
    if all(s == flat[0] for s in flat):
        addWin("cheio", full_pos, 50)

    return wins

@app.route("/rodar/<string:user_id>", methods=["POST"])
def rodar_machine(user_id):
    user = user_model.get_user_by_id(user_id)
    if not user:
        return jsonify({"error":"Usuário não encontrado"}),404

    user_balance = float(user.get("balance",0.0))

    bet_raw = request.json.get("bet") if request.json else 0.5
    try:
        bet = max(0.01, float(bet_raw))
    except:
        bet = 0.5

    if user_balance < bet:
        return jsonify({"error":"Saldo insuficiente"}),400

    grid = generate_grid()
    wins = check_wins(grid)

    total_win = 0.0
    mega_win = False

    for w in wins:
        c,r = w["positions"][0]
        symbol = grid[c][r]
        total_win += bet * SYMBOL_VALUES[symbol] * w["payout"]
        if w["type"] == "cheio":
            mega_win = True

    free_spins = 10 if mega_win else 0
    message = "MEGA WIN" if mega_win else ""

    if total_win > 0:
        new_balance = user_balance + total_win
        machine.balance -= total_win
    else:
        new_balance = user_balance - bet
        machine.balance += bet

    user_model.update_user(user_id, {"balance": float(new_balance)})

    return jsonify({
        "grid": grid,
        "win": round(total_win,2),
        "balance_user": round(new_balance,2),
        "balance_machine": round(machine.balance,2),
        "wins": wins,
        "level": LEVEL,
        "mega_win": mega_win,
        "free_spins": free_spins,
        "message": message
        
    })





#=======================================================
# -PAINEL DE CONTROLE ACESSO
#=======================================================
@app.route("/acesso/users/painel/<string:user_id>")
def acesso_users_painel(user_id):
    # Busca o usuário pelo ID
    user = user_model.get_user_by_id(user_id)

    if user:
        nome_value = user.get('nome')
        cpf_value = user.get('cpf')
        balance_value = user.get('balance')
        if balance_value is None:
            balance_value = ""  # ou "-" se quiser
        else:
            balance_value = f"{balance_value:.2f}"
        
        return render_template(
            "painel_game.html",
            user_id=user_id,
            nome=nome_value,
            cpf=cpf_value,
            balance=balance_value
        )
    else:
        return "Nenhum usuário encontrado no banco de dados."
#==========================================================
# -ROTA MAQUINA Fortune dollar
#==========================================================
# ================= SOCKET =================

# ================= ROTA ===================
@app.route("/acesso/users/<string:user_id>")
def acesso_users_machine(user_id):
    user = user_model.get_user_by_id(user_id)
    if not user:
        return "Usuário não encontrado"

    balance = user.get("balance")
    balance = "" if balance is None else f"{balance:.2f}"

    nome = user.get("nome") or ""
    cidade = user.get("cidade") or ""

    return render_template(
        "slotmachine_dollar.html",
        user_id=user_id,
        balance=balance,
        nome=nome,
        cidade=cidade
    )


# ============== SOCKET.IO =================
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on("join_users")
def join_users(data):
    user_id = str(data["user_id"])

    user = user_model.get_user_by_id(user_id)
    if not user:
        return

    emit(
        "user_conectado",
        {
            "user_id": user_id,
            "nome": user.get("nome", ""),
            "cidade": user.get("cidade", ""),
            "balance": f"{user.get('balance', 0):.2f}"
        },
        broadcast=True
    )

#==========================================================
# -ROTA MAQUINA Fortune Era Egpcia
#==========================================================
@app.route("/acesso/users/3x3/<string:user_id>")
def acesso_users_machine3x3(user_id):
    user = user_model.get_user_by_id(user_id)

    if user:
        # Pega o balance do banco
        balance_value = user.get('balance')

        # Se for None ou inválido, não mostra 0, pode mostrar vazio ou "-"
        if balance_value is None:
            balance_value = ""  # ou "-" se quiser
        else:
            # Formata com duas casas decimais
            balance_value = f"{balance_value:.2f}"

        return render_template("slotmachine3x3.html", user_id=user_id, balance=balance_value)
    else:
        return "Usuário não encontrado"       

@app.route("/informacao/jogo/era_egpcia/<string:user_id>")
def informacao_era_egpcia(user_id):
    return render_template("help/informacao_era_egpcia.html", user_id=user_id)
#==========================================================
# -ROTA MAQUINA Fortune duends
#==========================================================
@app.route("/acesso/users/fortune/duends/<string:user_id>")
def acesso_users_machine_duends(user_id):
    user = user_model.get_user_by_id(user_id)

    if user:
        # Pega o balance do banco
        balance_value = user.get('balance')

        # Se for None ou inválido, não mostra 0, pode mostrar vazio ou "-"
        if balance_value is None:
            balance_value = ""  # ou "-" se quiser
        else:
            # Formata com duas casas decimais
            balance_value = f"{balance_value:.2f}"

        return render_template("slotmachine_duends.html", user_id=user_id, balance=balance_value)
    else:
        return "Usuário não encontrado"

#==========================================================
# -ROTA MAQUINA Fortune Cofre Premiado "diveros"
#==========================================================
@app.route("/acesso/users/fortune/cofre/<string:user_id>")
def acesso_users_machine_cofre(user_id):
    user = user_model.get_user_by_id(user_id)

    if user:
        # Pega o balance do banco
        balance_value = user.get('balance')

        # Se for None ou inválido, não mostra 0, pode mostrar vazio ou "-"
        if balance_value is None:
            balance_value = ""  # ou "-" se quiser
        else:
            # Formata com duas casas decimais
            balance_value = f"{balance_value:.2f}"

        return render_template("slotmachine_diversos.html", user_id=user_id, balance=balance_value)
    else:
        return "Usuário não encontrado"
#==========================================================
# -ROTA MAQUINA Fortune Poker Girls
#==========================================================
@app.route("/acesso/users/fortune/poker/<string:user_id>")
def acesso_users_machine_poker_girls(user_id):
    user = user_model.get_user_by_id(user_id)

    if user:
        # Pega o balance do banco
        balance_value = user.get('balance')

        # Se for None ou inválido, não mostra 0, pode mostrar vazio ou "-"
        if balance_value is None:
            balance_value = ""  # ou "-" se quiser
        else:
            # Formata com duas casas decimais
            balance_value = f"{balance_value:.2f}"

        return render_template("slotmachine_duends.html", user_id=user_id, balance=balance_value)
    else:
        return "Usuário não encontrado"
          
#============================================================
# -MOVIMENTACOES DENTRO APP
#============================================================
@app.route("/acesso/users/pagamentos/<string:user_id>")
def acesso_users_movimentacoes(user_id):
    # Busca o usuário pelo ID
    user = user_model.get_user_by_id(user_id)
    

    if user:
        nome_value = user.get('nome')
        cpf_value = user.get('cpf')
        balance_value = user.get('balance', 0)

        return render_template(
            "movimentacoes.html",
            user_id=user_id,
            nome=nome_value,
            cpf=cpf_value,
            balance=balance_value
        )
    else:
        return "Nenhum usuário encontrado no banco de dados."

#=====================================================
# saques
#=====================================================

@app.route("/acesso/users/saques/<string:user_id>")
def acesso_users_saques(user_id):
    user = user_model.get_user_by_id(user_id)

    if not user:
        return "Nenhum usuário encontrado no banco de dados."

    return render_template(
        "saques.html",
        user_id=user_id,
        nome=user.get("nome"),
        cpf=user.get("cpf"),
        chave_pix=user.get("chave_pix"),
        balance=user.get("balance", 0)
    )


@app.route("/saque/<string:user_id>", methods=["POST"])
def sacar(user_id):
    try:
        data = request.get_json()
        valor_saque = data.get("valor_saque")

        if not isinstance(valor_saque, (int, float)) or valor_saque <= 0:
            return jsonify({"error": "Valor de saque inválido"}), 400

        try:
            object_id = ObjectId(user_id)
        except:
            return jsonify({"error": "ID inválido"}), 400

        result = user_model.collection.find_one_and_update(
            {
                "_id": object_id,
                "balance": {"$gte": valor_saque}
            },
            {
                "$inc": {"balance": -valor_saque}
            },
            return_document=True
        )

        if not result:
            return jsonify({"error": "Saldo insuficiente"}), 400

        return jsonify({
            "message": "Saque realizado com sucesso",
            "novo_saldo": result["balance"]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/compra/raffle/balance/diponivel/<string:user_id>", methods=["POST"])
def compra_raffle_balance(user_id):
    try:
        data = request.get_json()
        valor = data.get("valor_total")

        if not isinstance(valor, (int, float)) or valor <= 0:
            return jsonify({"error": "Valor Balance  inválido"}), 400

        try:
            object_id = ObjectId(user_id)
        except:
            return jsonify({"error": "ID inválido"}), 400

        result = user_model.collection.find_one_and_update(
            {
                "_id": object_id,
                "balance": {"$gte": valor}
            },
            {
                "$inc": {"balance": -valor}
            },
            return_document=True
        )

        if not result:
            return jsonify({"error": "Saldo insuficiente"}), 400

        return jsonify({
            "message": "Compra realizada com sucesso",
            "novo_saldo": result["balance"]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


#========================================================================================================
# -PUT ( ATUALIZAR COMPRAS_RF "PAGAMENTO_APROVADO")
#========================================================================================================
# @app.route('/atualizar/compras_rf/pagamento_aprovado/<string:user_id>', methods=["PUT"])
# def atualizar_compras_rf_pagamento(user_id):
#     data = request.get_json()
# 
#     if "pagamento_aprovado" not in data or not data["pagamento_aprovado"]:
#         return jsonify({"error": "Campo obrigatório: pagamento_aprovado"}), 400
# 
#     result = compras_rf_model.update_pagamento_aprovado(
#         user_id=user_id,
#         status=data["pagamento_aprovado"]
#     )
# 
#     if not result:
#         return jsonify({"error": "Compra não encontrada"}), 404
# 
#     return jsonify({"status": "ok"}), 200


#========================================================================
# -DELETE APOS 1HORA DELETA TODAS COMPRA_RF PENDENTE
#========================================================================
# @app.route('/delete/compras_rf/pagamento_aprovado/pendente/<string:user_id>', methods=["DELETE"])
# def delete_compras_rf_pendente(user_id):
#     limite = datetime.now() - timedelta(hours=1)
# 
#     deletados = compras_rf_model.delete_pendentes_antes_1h(
#         user_id=user_id,
#         limite=limite
#     )
# 
#     return jsonify({"deletados": deletados}), 200


#=======================================================================
# GET MOSTRAR TODAS COMPRAS_RF APPROVED BUSCAR POR EMAIL
#=======================================================================
# @app.route('/buscar/compras_rf/pagamento_aprovado/approved/<string:user_id>', methods=["GET"])
# def buscar_compras_rf_aprovadas(user_id):
#     user = user_model.get_user_by_id(user_id)
#     if not user:
#         return jsonify({"error": "Usuário não encontrado"}), 404
# 
#     email_user = user.get("email")
# 
#     compras = compras_rf_model.get_approved_by_email(email_user)
# 
#     return jsonify(compras), 200

#==============================================================
# tela inicial raffles
@app.route("/index/users/<string:user_id>")
def raffle_inicio(user_id):
    sorteio = sorteio_model.collection.find_one({}, sort=[("_id", -1)])
    # proximoSorteio = sorteio_model.get_sorteio_by_id(sorteio_id)
    concurso_value = sorteio.get('concurso') if sorteio else ""
    data_value = sorteio.get('data') if sorteio else ""
    dezenas_value = sorteio.get('dezenas') if sorteio else []
    proximoConcurso_value = sorteio.get('proximoConcurso') if sorteio else ""
    dataProximoConcurso_value = sorteio.get('dataProximoConcurso') if sorteio else ""
   
        
    return render_template("rifa/index.html", user_id=user_id, concurso=concurso_value,data=data_value, dezenas=dezenas_value, proximoConcurso=proximoConcurso_value, dataProximoConcurso=dataProximoConcurso_value)
#===============================================================

#==============================================================
# tela comprar raffles 
@app.route("/users/produto/<string:user_id>")
def raffle(user_id):
    sorteio = sorteio_model.collection.find_one({}, sort=[("_id", -1)])
    user = user_model.get_user_by_id(user_id)
    proximoConcurso_value = sorteio.get('proximoConcurso') if sorteio else ""
    dataProximoConcurso_value = sorteio.get('dataProximoConcurso') if sorteio else ""

    if user:
        balance_value = user.get('balance')
        if balance_value is None:
            balance_value = ""  # ou "-" se quiser
        else:
            balance_value = f"{balance_value:.2f}"
        
        return render_template(
            "rifa/raffle.html",
            user_id=user_id,
            balance=balance_value,
            proximoConcurso=proximoConcurso_value,
            dataProximoConcurso=dataProximoConcurso_value
        )
    else:
        return "Nenhum usuário encontrado no banco de dados."





@app.route("/review/users/<string:user_id>")
def review_compra(user_id):

    # Buscar a última compra desse usuário
    compra_rf = compras_rf_model.collection.find_one(
        {"user_id": user_id},
        sort=[("_id", -1)]
    )

    user = user_model.get_user_by_id(user_id)

    nome_value = user.get('nome') if user else ""
    cpf_value = user.get('cpf') if user else ""
    email_value = user.get('email') if user else ""

    # Se não existir compra ainda
    if not compra_rf:
        return render_template(
            "rifa/review.html",
            user_id=user_id,
            nome=nome_value,
            balance=user.get("balance", 0),
            cpf=cpf_value,
            email=email_value,
            valor=0,
            valor_final=0,
            quantity=0,
            tickets=[]
        )

    return render_template(
        "rifa/review.html",
        user_id=user_id,
        nome=nome_value,
        cpf=cpf_value,
        email=email_value,
        balance=user.get("balance", 0),
        valor=compra_rf.get("valor_unit"),
        valor_final=compra_rf.get("valor"),
        quantity=compra_rf.get("quantity"),
        tickets=compra_rf.get("tickets", [])
    )
                   



#====================================================================================================
# - COMPRAS_RF POST
#====================================================================================================
@app.route("/compras_rf/<string:user_id>", methods=["POST"])
def create_purchase(user_id):
    data = request.get_json()

    required_fields = ["tickets", "valor", "quantity"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"Campo obrigatório: {field}"}), 400

    user = user_model.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    new_compras_rf = {
        "user_id": user_id,
        "cpf": user.get("cpf"),
        "email_user": user.get("email"),
        "data_sorteio": data.get("data_sorteio"),
        "tickets": data["tickets"],
        "pagamento_id": None,              
        # "codigo": data.get("codigo"),
        "valor": data["valor"],
        "quantity": data["quantity"],
        "created_at": datetime.utcnow()
    }

    compras_rf_id = compras_rf_model.create_compras_rf(new_compras_rf)
    return jsonify({"id": compras_rf_id}), 201
#===========================================================
# -PAGAMENTO VIA SOMENTE PIX PREFERENCE MERCADO´PAGO 
#===========================================================

















#=======================================================================
#=======================================================================
# COMPRA DE BALANCE API MERCADO PAGO 

@app.route('/comprar_saldo')
def comprarSaldo():
    return render_template("compra_balance.html")
    
    
@app.route('/create_payment_preference', methods=['POST'])
def create_payment_preference():
    data = request.get_json()
    amount = data.get('amount')
    user_id = data.get('user_id')

    preference_data = {
        "items": [
            {
                "title": "Livro",
                "quantity": 1,
                "unit_price": float(amount)
            }
        ],
        #Configura a URL notifiaçao 
        "notification_url": f"https://ferrari-games-itech-io.onrender.com/notificacoes{user_id}",
        "external_reference": user_id # Armazena o ID do usuario para referencia
    }

    preference_response = sdk.preference().create(preference_data)
    preference = preference_response["response"]

    return jsonify({"preference_id": preference["id"]})


@app.route('/notificacoes', methods=["POST"])    
def mercadopago_webhook():
    data = request.get_json()
    payment_id = data.get('data', {}).get('id')

    if payment_id:
        payment_info = sdk.payment().get(payment_id)
        status = payment_info["response"]["status"]
        user_id = payment_info["response"].get("external_reference")
        amount = payment_info["response"].get("transaction_amount", 0)

        if status == "approved":
            users_collection.update_one(
                {"_id": user_id},
                {"$inc": {"balance": float(amount)}}
            )
            msg = f"Saldo do usuário {user_id} atualizado com {amount}!"
            print(msg)

            socketio.emit(
                "payment_update",
                {
                    "status": status,
                    "message": msg,
                    "payment_id": payment_id,
                    "amount": amount
                },
                room=payment_id
            )
            print(f"[WEBHOOK] {msg} | ID: {payment_id}")
            return jsonify({"status": "success"}), 200

    return jsonify({"status": "error"}), 400
#==========================================================================
#==========================================================================
#==========================================================================




       
@app.route("/compra/preference/pagamento_pix/<string:user_id>")
def pagamento_preference(user_id):
    nome = request.args.get("nome") or ""
    email = request.args.get("email") or ""
    cpf = request.args.get("cpf") or ""
    qtd = int(request.args.get("qtd") or 0)

    valor_total = qtd * 2.50

    # preference gerar_link_pagamento()
    payment_data = {
        "items": [
            {
                "id": user_id,
                "title": "Block Gold",
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": valor_total
            }
        ],
        "payer": {
            "email": email,
            "first_name": nome,
            "identification": {
                "type": "CPF",
                "number": cpf
            }
        },
        "external_reference": user_id,

        "back_urls": {
            "success": "https://ferrari-games-itech-io.onrender.com/compra/sucesso",
            "failure": "https://ferrari-games-itech-io.onrender.com/compra/recusada",
        },

        "notification_url": "https://ferrari-games-itech-io.onrender.com/notificacoes",
        "payment_methods": {
            "excluded_payment_types": [
                {"id": "credit_card"}
            ]
        }
    }

    result = sdk.preference().create(payment_data)
    mp = result.get("response", {})

    if "id" not in mp:
        return f"ERRO NO MERCADO PAGO:<br><br>{mp}", 500

    payment_id = mp["id"]
    status = "pending"

    documento = criar_documento_pagamento(
        payment_id=str(payment_id),
        status=status,
        valor=valor_total,
        user_id=user_id,
        email_user=email
    )

    PagamentoModel().create_pagamento(documento)

    # IGUAL seu exemplo → só retorna o link
    link_pagamento = mp.get("init_point", "")
    return link_pagamento




#===========================================================              
# -PAGAMENTO VIA SOMENTE PIX QRCODE               
#===========================================================              
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")              
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)              
              
# ===========================================
# GERAR QR CODE PIX
# ===========================================
@app.route("/payment_qrcode_pix/pagamento_pix/<string:user_id>")
def pagamento_pix(user_id):
    compra_rf = compras_rf_model.collection.find_one(
            {"user_id": user_id},
            sort=[("_id", -1)]
        )
    user = user_model.get_user_by_id(user_id)     
    

    nome = request.args.get("nome") or ""
    email = request.args.get("email") or ""
    cpf = request.args.get("cpf") or ""
    telefone = request.args.get("telefone") or ""
    qtd = int(request.args.get("qtd") or 0)

    amount = qtd * 0.05

    payment_data = {
        "transaction_amount": amount,
        "description": "Livro",
        "payment_method_id": "pix",
        "payer": {
            "email": email,
            "first_name": nome,
            "identification": {
                "type": "CPF",
                "number": cpf
            }
        },
        "external_reference": user_id,
        "notification_url": "https://ferrari-games-itech-io.onrender.com/notificacoes"
    }

    response = sdk.payment().create(payment_data)
    mp = response.get("response", {})

    if "id" not in mp:
        return f"ERRO NO MERCADO PAGO:<br><br>{mp}", 500

    payment_id = str(mp["id"])
    status = mp.get("status", "pending")

    documento = criar_documento_pagamento(
        payment_id=payment_id,
        status=status,
        valor=amount,
        user_id=user_id,
        email_user=email
       
        
    )

    PagamentoModel().create_pagamento(documento)

    tx = mp["point_of_interaction"]["transaction_data"]

    return render_template(
        "rifa/transaction_pix.html",
        qrcode=f"data:image/png;base64,{tx['qr_code_base64']}",
        valor=f"R$ {amount:.2f}",
        description="Livro",
        qr_code_cola=tx["qr_code"],
        status=status,
        payment_id=payment_id,
        user_id=user_id
    )
# ===========================================

# SOCKET.IO - SALA POR PAGAMENTO

# ===========================================

@socketio.on("join_payment")
def join_payment_room(data):
    room = data["payment_id"]
    join_room(room)



cloudinary.config(
    cloud_name="dptprh0xk",
    api_key="445146224712139",
    api_secret="f6_EFYbTpEy8SlV8BHyRqwuiEWA",
    secure=True
)

# Mensagens
@socketio.on('enviar_mensagem_frontend')
def handle_message(data):
    user_id = data.get('user_id', 'Anon')
    emit('receber_mensagem_backend', {
        'texto': data.get('texto'),
        'user_id': user_id,
        'tipo': 'recebida'
    }, broadcast=True)

@socketio.on('upload_audio')
def handle_audio_upload(audio_blob):
    # audio_blob é um objeto Bytes (buffer)

    try:
        # Salvar temporariamente para upload (ou manipular o buffer diretamente, se preferir)
        temp_file_path = "temp_audio.webm"
        with open(temp_file_path, "wb") as f:
            f.write(audio_blob)

        # Fazer upload para o Cloudinary
        # Define resource_type como 'video' para uploads de áudio/vídeo
        upload_result = cloudinary.uploader.upload(
            temp_file_path,
            resource_type="video", 
            folder="audio_uploads" # Pasta opcional no Cloudinary
        )

        # Limpar o arquivo temporário
        os.remove(temp_file_path)

        # Enviar a URL segura de volta para o cliente ou logar
        secure_url = upload_result.get('secure_url')
        print(f"Upload bem-sucedido: {secure_url}")
        socketio.emit('audio_uploaded', {'url': secure_url})

    except Exception as e:
        print(f"Erro no upload: {e}")
        socketio.emit('upload_error', {'message': 'Falha no upload do áudio'})

# ====================== IMAGEM ======================
@app.route('/api/save-image', methods=['POST'])
def save_imagem_rifa():
    data = request.get_json()
    imagem_rifa = data.get('imagem_comprovante')
    if imagem_rifa:
        print(f"URL recebida e salva no DB: {imagem_comprovante}")
        return jsonify({"message": "URL salva com sucesso"}), 200
    return jsonify({"error": "URL não fornecida"}), 400

# ===========================================
# WEBHOOK MERCADO PAGO 
# ===========================================

# ===========================================
# ATUALIZAR STATUS NO BANCO (ADICIONAR)
# ===========================================

def atualizar_status_pagamento(payment_id, status):
    PagamentoModel().collection.update_one(
        {"payment_id": str(payment_id)},
        {"$set": {"status": status}}
    )


# ===========================================
# WEBHOOK MERCADO PAGO (ADICIONAR LINHAS)
# ===========================================

# @app.route("/notificacoes", methods=["POST"])
# def handle_webhook():
#     data = request.json
#     if not data:
#         return "", 204
# 
#     if data.get("type") == "payment":
#         payment_id = data["data"]["id"]
#         payment_details = get_payment_details(payment_id)
#         if not payment_details:
#             return "", 204
# 
#         status = payment_details.get("status")
# 
#         
# 
#         atualizar_status_pagamento(payment_id, status)
# 
#         if status == "approved":
#             msg = "Pagamento aprovado"
#         else:
#             msg = f"Status atualizado: {status}"
#             
# 
# 
# 
#           # Logica para atualizar o saldo "balance " no MongoDB
#           users_collection.update_one(
#             {"_id": user_id},
#             {"$inc": {"balance": float(amount)}}
#           )
#           print(f"Saldo do usuario {user_id} atualizado com sucesso!")            
# 
# 
#             
# 
#         socketio.emit(
#             "payment_update",
#             {
#                 "status": status,
#                 "message": msg,
#                 "payment_id": payment_id
#             },
#             room=payment_id
#         )
# 
#         print(f"[WEBHOOK] {msg} | ID: {payment_id}")
# 
#     return "", 204
# ===========================================

def get_payment_details(payment_id):
    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}"
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    return None

#=======================================================================
# ATUALIZAR BALANCE COM VALOR APPROVED 
#=======================================================================
@app.route("/deposito/atualizado/balance/<string:user_id>", methods=["POST"])
def deposito(user_id):
    try:
        data = request.get_json()
        valor_total = data.get("valor_total")

        if not isinstance(valor_total, (int, float)) or valor_total <= 0:
            return jsonify({"error": "valor inválido"}), 400

        try:
            object_id = ObjectId(user_id)
        except:
            return jsonify({"error": "ID inválido"}), 400

        result = user_model.collection.find_one_and_update(
            {"_id": object_id},
            {"$inc": {"balance": valor_total}},
            return_document=True
        )

        if not result:
            return jsonify({"error": "usuário não encontrado"}), 404

        return jsonify({
            "message": "saldo atualizado com sucesso",
            "novo_saldo": result["balance"]
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/compra/sucesso')
def success():
    return render_template("/loading.html")
#=================================================================================================
    
#----------------------------------------------------------
# -PAGAMENTO RECUSADO
#----------------------------------------------------------

@app.route("/compra/recusada")
def preference_payment_success():
    return render_template("rifa/recusada.html")
    
@app.route("/compra/recusada/<string:user_id>")
def compra_recusada_raffle(user_id):
    return render_template("rifa/recusada.html", user_id=user_id)


@app.route("/assinatura/<string:user_id>")    
def assinatura(user_id):
    return render_template("assinatura_raffles.html",user_id=user_id)
#===========================================================================================
# -CRUD USERS MACHINEs
#===========================================================================================
#===========================
# CRIAR COLABORADORES ADMIN
#===========================
@app.route("/adm", methods=["POST"])
def register_admin():
    data = request.get_json()
    required = ["nome","sobrenome","cpf","data_nascimento","email","senha"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"Campo obrigatório: {field}"}), 400
    cpf_digits = re.sub(r"\D", "", data["cpf"])
    exists = admin_model.get_admin_by_cpf(cpf_digits)
    if exists:
        return jsonify({"error": "CPF já registrado"}), 409

    new_admin = {
        "nome": data["nome"],
        "sobrenome": data["sobrenome"],
        "cpf": cpf_digits,
        "data_nascimento": data["data_nascimento"],
        "email": data["email"],
        "convite": data.get("convite",""),
        "chave_pix": data.get("chave_pix",""),
        "senha": data["senha"],
        "saldo": 0.0,
        "created_at": datetime.now()
    }
    admin_id = admin_model.create_admin(new_admin)
    return jsonify({"id": admin_id}), 201


#========================================
# LOGIN CPF
#========================================
@app.route("/login/admin", methods=["POST"])
def login_admin():
    data = request.get_json()
    cpf = data.get("cpf", "")

    cpf_digits = re.sub(r"\D", "", cpf)
    admin = admin_model.get_admin_by_cpf(cpf_digits)

    if not admin:
        return jsonify({"error": "Admin não encontrado"}), 404

    return jsonify({
        "redirect": f"/admin_dashboard/{admin['_id']}"
    })

#===========================
# LOGIN PÁGINA HTML
#===========================
@app.route("/login")
def login_administradores():
    return render_template("rifa/admin_dashboard/login.html")



@app.route("/ferrari/full/users", methods=["GET"])
def users_full():
    users = user_model.get_all_users()
    pagamentos = pagamento_model.get_all_pagamentos()
    

    pag_map = {}
    for p in pagamentos:
        uid = str(p.get("user_id"))
        pag_map.setdefault(uid, []).append(p)

   

    full = []
    for u in users:
        uid = str(u.get("_id"))
        full.append({
            "user": u,
            "pagamentos": pag_map.get(uid, []),
            
        })

    return jsonify(full), 200
            
@app.route('/users', methods=['GET'])
def get_users():
    users = user_model.get_all_users()
    return jsonify(users), 200

@app.route('/sorteio', methods=['GET'])
def get_sorteios():
    sorteio = sorteio_model.get_all_sorteio()
    return jsonify(sorteio), 200
#----------------------------------------‐------
@app.route('/pagamentos/pix', methods=['GET'])
def get_pagamentos():
    pagamentos = pagamento_model.get_all_pagamentos()
    return jsonify(pagamentos), 200

#===========================  
# DASHBOARD ADMIN PRINCIPAL  
#===========================  
@app.route("/admin_dashboard/<string:admin_id>")  
def admin(admin_id):  
    admin = admin_model.get_admin_by_id(admin_id)

    # Total de usuários
    total_users = len(user_model.get_all_users())  # pega todos os usuários e conta

    # Total arrecadado (somente pagamentos aprovados)
    all_payments = pagamento_model.get_all_pagamentos()  # pega todos os pagamentos
    pagamentos_aprovados = [p for p in all_payments if p.get('status') == 'aprovado']
    total_arrecadado = sum(p['valor'] for p in pagamentos_aprovados)

    # Total de tickets vendidos
    all_tickets = compras_rf_model.get_all_compras_rf()  # pega todas as compras
    total_tickets = sum(c['quantity'] for c in all_tickets)  # soma a quantidade de tickets corretamente

    if admin:
        nome_value = admin.get('nome')
        cpf_value = admin.get('cpf')
        convite_value = admin.get('convite')

        return render_template(
            "rifa/admin_dashboard/dashboard-admin.html",
            payment_id=None, 
            admin_id=admin_id,
            nome=nome_value,
            cpf=cpf_value,
            convite=convite_value,
            total_users=total_users,
            total_arrecadado=total_arrecadado,
            total_tickets=total_tickets
        )
    else:
        return "Nenhum admin encontrado no banco de dados."





#===================================================
# -CREATE-RAFFLE
#===================================================
@app.route('/admin_dashboard/create-raffle/<string:admin_id>')
def painel_create_raffles(admin_id):
    return render_template("rifa/admin_dashboard/create-raffle.html", admin_id=admin_id)

#====================================================
#-USERS
#===================================================
@app.route('/admin_dashboard/painel/participants/<string:admin_id>')
def painel_get_users_compras_rf(admin_id):
    return render_template("rifa/admin_dashboard/participants.html", admin_id=admin_id)




@app.route('/admin_dashboard/list-raffles/<string:admin_id>')
def painel_list_raffles(admin_id):
    return render_template("rifa/admin.html", admin_id=admin_id)    

    
#===========================  
# PAGAMENTOS ADMIN  
#===========================  
@app.route('/dashboard/admin/pagamentos/<string:payment_id>')
def dash(payment_id):
    users = user_model.get_all_users()
    pagamentos = pagamento_model.get_all_pagamentos()

    # Primeiro mapeia pagamentos por user_id (igual users/full)
    pag_map = {}
    for p in pagamentos:
        uid = str(p.get("user_id"))
        pag_map.setdefault(uid, []).append(p)

    # Agora monta a lista cheia igual users/full
    full = []
    for u in users:
        uid = str(u.get("_id"))
        full.append({
            "user": u,
            "pagamentos": pag_map.get(uid, [])
        })

    # Agora procura o pagamento específico solicitado
    pagamento_escolhido = None
    for p in pagamentos:
        if p.get("payment_id") == payment_id:
            pagamento_escolhido = p
            break

    return render_template(
        "rifa/admin_dashboard/payments.html",
        payment_id=payment_id,
        pagamento=pagamento_escolhido,
        full=full
    )

@app.route("/collections", methods=["GET"])
def list_mongo_collections():
    """
    Rota para listar todas as coleções no banco de dados MongoDB.
    """
    try:
        # Usa list_collection_names() para obter uma lista simples de nomes
        collection_names = db.list_collection_names()
        
        # Ou use db.list_collections() para obter cursores com metadados
        # collections_metadata = list(db.list_collections())
        
        return jsonify({
            "database": DB_NAME,
            "collections": collection_names,
            "count": len(collection_names)
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

#===========================================
# -Run
#===========================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=True,
        allow_unsafe_werkzeug=True
    )
