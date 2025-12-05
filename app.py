from flask import Flask, request, jsonify, abort, render_template, redirect,  url_for
import mercadopago
from io import BytesIO
import base64
import qrcode
from collections import defaultdict
from datetime import datetime, timezone, timedelta
# from datetime import datetime
from model import UsuarioModel, AdminModel, Compras_rfModel,SorteioModel, PagamentoModel, pagamentos_collection, criar_documento_pagamento
from bson.errors import InvalidId
import os
import re
import json
from bson.objectid import ObjectId
from flask_cors import CORS
import random
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta' 
user_model = UsuarioModel()
pagamento_model = PagamentoModel()
admin_model = AdminModel()
compras_rf_model = Compras_rfModel()
sorteio_model = SorteioModel()
os.makedirs('static/images', exist_ok=True)
os.makedirs('static/upload', exist_ok=True)


app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)


#============================================================================================
#============================================================================================
# -------------------------------------------------------------------------------------------
# MAQUINA 5x3
# -------------------------------------------------------------------------------------------
LEVEL_5X3 = 1

SYMBOL_NAMES_5X3 = [
    "pato","ganso","coruja","papagaio","pombo",
    "andorinha","gaivota","beija-flor","pavão","tucano",
    "pardal","corvo","flamingo","rouxinol","galinha"
]

class Machine5x3:
    def __init__(self, balance=500.0):
        self.balance = float(balance)

machine_5x3 = Machine5x3()

def random_symbol_5x3():
    return random.choice(SYMBOL_NAMES_5X3)

def generate_grid_5x3():
    # grid[c][r] com c em 0..4 (5 colunas) e r em 0..2 (3 linhas)
    cols, rows = 5, 3
    grid = [[random_symbol_5x3() for r in range(rows)] for c in range(cols)]

    # Aplicar facilitação similar ao LEVEL da 5x5, mas adaptada
    if LEVEL_5X3 == 1:
        # facilitar colunas
        for c in range(cols):
            sym = random_symbol_5x3()
            for r in range(rows):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]
        # facilitar linhas
        for r in range(rows):
            sym = random_symbol_5x3()
            for c in range(cols):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]
        # diagonais (comprimento = min(cols,rows) = 3)
        sym = random_symbol_5x3()
        for i in range(min(cols, rows)):
            grid[i][i] = sym if random.randint(0,1) else grid[i][i]
        sym = random_symbol_5x3()
        for i in range(min(cols, rows)):
            grid[cols - min(cols,rows) + i][i] = sym if random.randint(0,1) else grid[cols - min(cols,rows) + i][i]
        # cruzado X (cantos + centro da área 3x3 no canto esquerdo)
        sym = random_symbol_5x3()
        cross_positions = [(0,0),(2,2),(0,2),(2,0),(1,1)]
        for c,r in cross_positions:
            if c < cols and r < rows:
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]
        # borda top/bottom
        sym = random_symbol_5x3()
        borda_positions = [(c,0) for c in range(cols)] + [(c,rows-1) for c in range(cols)]
        for c,r in borda_positions:
            grid[c][r] = sym if random.randint(0,1) else grid[c][r]

    elif LEVEL_5X3 == 2:
        for c in range(cols):
            sym = random_symbol_5x3()
            for r in range(rows):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]
    elif LEVEL_5X3 == 3:
        for c in range(cols):
            sym = random_symbol_5x3()
            for r in range(rows):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]

    return grid

def check_wins_5x3(grid):
    wins = []
    cols, rows = 5, 3

    def addWin(type_, positions):
        multiplier = 0
        if type_ == "horizontal": multiplier = 5
        elif type_ == "vertical": multiplier = 8
        elif type_ in ("diagonal_principal", "diagonal_invertida"): multiplier = 12
        elif type_ == "cruzado_x": multiplier = 20
        elif type_ == "borda": multiplier = 15
        elif type_ == "cheio": multiplier = 50

        wins.append({
            "type": type_,
            "positions": positions,
            "payout": multiplier
        })

    # horizontais (cada linha tem cols símbolos iguais)
    for r in range(rows):
        if all(grid[c][r] == grid[0][r] for c in range(cols)):
            addWin("horizontal", [(c,r) for c in range(cols)])

    # verticais (cada coluna tem rows símbolos iguais)
    for c in range(cols):
        if all(grid[c][r] == grid[c][0] for r in range(rows)):
            addWin("vertical", [(c,r) for r in range(rows)])

    # diagonais (comprimento = rows = 3)
    # diagonal principal (0,0),(1,1),(2,2)
    diag_pr = [(i,i) for i in range(min(cols,rows))]
    if all(grid[c][r] == grid[diag_pr[0][0]][diag_pr[0][1]] for (c,r) in diag_pr):
        addWin("diagonal_principal", diag_pr)

    # diagonal invertida: usar a faixa direita que tenha tamanho 3: (cols-3,0),(cols-2,1),(cols-1,2)
    diag_inv = [(cols - min(cols,rows) + i, i) for i in range(min(cols,rows))]
    if all(grid[c][r] == grid[diag_inv[0][0]][diag_inv[0][1]] for (c,r) in diag_inv):
        addWin("diagonal_invertida", diag_inv)

    # cruzado X na subárea 3x3 do canto (0..2,0..2)
    cross_positions = [(0,0),(2,2),(0,2),(2,0),(1,1)]
    if all(grid[c][r] == grid[cross_positions[0][0]][cross_positions[0][1]] for (c,r) in cross_positions):
        addWin("cruzado_x", cross_positions)

    # borda top+bottom
    borda_positions = [(c,0) for c in range(cols)] + [(c,rows-1) for c in range(cols)]
    borda_vals = [grid[c][r] for (c,r) in borda_positions]
    if all(s == borda_vals[0] for s in borda_vals):
        addWin("borda", borda_positions)

    # cheio (todas as células iguais)
    full_positions = [(c,r) for c in range(cols) for r in range(rows)]
    flat = [grid[c][r] for (c,r) in full_positions]
    if all(s == flat[0] for s in flat):
        addWin("cheio", full_positions)

    return wins

@app.route("/rodar_5x3/<string:user_id>", methods=["POST"])
def rodar_5x3(user_id):
    user = user_model.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    user_balance = float(user.get("balance", 0.0))
    bet_raw = request.json.get("bet") if request.json else 0.5
    try:
        bet = max(0.01, float(bet_raw))
    except:
        bet = 0.5

    if user_balance < bet:
        return jsonify({"error": "Saldo insuficiente"}), 400

    grid = generate_grid_5x3()
    wins = check_wins_5x3(grid)
    total_win = bet * len(wins) * 10.0 if wins else 0.0

    if total_win > 0:
        new_balance = user_balance + total_win
        machine_5x3.balance -= total_win
    else:
        new_balance = user_balance - bet
        machine_5x3.balance += bet

    user_model.update_user(user_id, {"balance": float(new_balance)})

    return jsonify({
        "grid": grid,
        "win": round(total_win, 2),
        "balance_user": round(new_balance, 2),
        "balance_machine": round(machine_5x3.balance, 2),
        "wins": wins,
        "level": LEVEL_5X3
    })

#==================================================================================================
#==================================================================================================
# -------------------------------------------------------------------------------------------------
# MAQUINA 3x3 
# ------------------------------------------------------------------------------------------------
LEVEL_3X3 = 1

SYMBOL_NAMES_3X3 = [
    "estrela","lua","sol","cometa","planeta","asteroide","meteoro"
]

class Machine3x3:
    def __init__(self, balance=300.0):
        self.balance = float(balance)

machine_3x3 = Machine3x3()

def random_symbol_3x3():
    return random.choice(SYMBOL_NAMES_3x3 := SYMBOL_NAMES_3X3)  # alias para clareza

def generate_grid_3x3():
    cols, rows = 3, 3
    grid = [[random_symbol_3x3() for r in range(rows)] for c in range(cols)]

    if LEVEL_3X3 == 1:
        # facilitar linhas e colunas e diagonais
        for c in range(cols):
            sym = random_symbol_3x3()
            for r in range(rows):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]
        for r in range(rows):
            sym = random_symbol_3x3()
            for c in range(cols):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]
        sym = random_symbol_3x3()
        for i in range(rows):
            grid[i][i] = sym if random.randint(0,1) else grid[i][i]
        sym = random_symbol_3x3()
        for i in range(rows):
            grid[cols-1-i][i] = sym if random.randint(0,1) else grid[cols-1-i][i]
    elif LEVEL_3X3 == 2:
        for c in range(cols):
            sym = random_symbol_3x3()
            for r in range(rows):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]
    elif LEVEL_3X3 == 3:
        for c in range(cols):
            sym = random_symbol_3x3()
            for r in range(rows):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]

    return grid

def check_wins_3x3(grid):
    wins = []
    cols, rows = 3, 3

    def addWin(type_, positions):
        multiplier = 0
        if type_ == "horizontal": multiplier = 5
        elif type_ == "vertical": multiplier = 8
        elif type_ in ("diagonal_principal", "diagonal_invertida"): multiplier = 12
        elif type_ == "cruzado_x": multiplier = 20
        elif type_ == "cheio": multiplier = 50

        wins.append({
            "type": type_,
            "positions": positions,
            "payout": multiplier
        })

    # horizontais
    for r in range(rows):
        if all(grid[c][r] == grid[0][r] for c in range(cols)):
            addWin("horizontal", [(c,r) for c in range(cols)])

    # verticais
    for c in range(cols):
        if all(grid[c][r] == grid[c][0] for r in range(rows)):
            addWin("vertical", [(c,r) for r in range(rows)])

    # diagonais
    diag_pr = [(i,i) for i in range(rows)]
    if all(grid[c][r] == grid[diag_pr[0][0]][diag_pr[0][1]] for (c,r) in diag_pr):
        addWin("diagonal_principal", diag_pr)

    diag_inv = [(cols-1-i, i) for i in range(rows)]
    if all(grid[c][r] == grid[diag_inv[0][0]][diag_inv[0][1]] for (c,r) in diag_inv):
        addWin("diagonal_invertida", diag_inv)

    # cruzado X: cantos + centro
    cross_positions = [(0,0),(2,2),(0,2),(2,0),(1,1)]
    if all(grid[c][r] == grid[cross_positions[0][0]][cross_positions[0][1]] for (c,r) in cross_positions):
        addWin("cruzado_x", cross_positions)

    # cheio
    full_positions = [(c,r) for c in range(cols) for r in range(rows)]
    flat = [grid[c][r] for (c,r) in full_positions]
    if all(s == flat[0] for s in flat):
        addWin("cheio", full_positions)

    return wins

@app.route("/rodar_3x3/<string:user_id>", methods=["POST"])
def rodar_3x3(user_id):
    user = user_model.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    user_balance = float(user.get("balance", 0.0))
    bet_raw = request.json.get("bet") if request.json else 0.5
    try:
        bet = max(0.01, float(bet_raw))
    except:
        bet = 0.5

    if user_balance < bet:
        return jsonify({"error": "Saldo insuficiente"}), 400

    grid = generate_grid_3x3()
    wins = check_wins_3x3(grid)
    total_win = bet * len(wins) * 10.0 if wins else 0.0

    if total_win > 0:
        new_balance = user_balance + total_win
        machine_3x3.balance -= total_win
    else:
        new_balance = user_balance - bet
        machine_3x3.balance += bet

    user_model.update_user(user_id, {"balance": float(new_balance)})

    return jsonify({
        "grid": grid,
        "win": round(total_win, 2),
        "balance_user": round(new_balance, 2),
        "balance_machine": round(machine_3x3.balance, 2),
        "wins": wins,
        "level": LEVEL_3X3
    })
#========================================================
# -LEVEL MAQUINA 5X5
#========================================================
LEVEL = 1

SYMBOL_NAMES = [
    "avestruz","aguia","burro","borboleta","cachorro",
    "cabra","carneiro","camelo","cobra","coelho",
    "galo","cavalo","elefante","gato","jacare",
    "leao","macaco","porco","pavao","peru",
    "tigre","touro","urso","veado","vaca"
]


class Machine:
    def __init__(self, balance=1000.0):
        self.balance = float(balance)

machine = Machine()

def random_symbol():
    return random.choice(SYMBOL_NAMES)
#==================================================================================
# ---------------------------------------------------------------------------------
# GERADOR COM VOLATILIDADE LEVEL
# ---------------------------------------------------------------------------------
def generate_grid():
    grid = [[random_symbol() for r in range(5)] for c in range(5)]

    # Facilitação de padrões conforme LEVEL
    if LEVEL == 1:
        # Facilita vertical, horizontal, diagonal, cruzado, janela, janelao, cheio
        for c in range(5):
            sym = random_symbol()
            for r in range(5):
                grid[c][r] = sym if random.randint(0, 1) else grid[c][r]
        for r in range(5):
            sym = random_symbol()
            for c in range(5):
                grid[c][r] = sym if random.randint(0, 1) else grid[c][r]
        sym = random_symbol()
        for i in range(5):
            grid[i][i] = sym if random.randint(0, 1) else grid[i][i]
        sym = random_symbol()
        for i in range(5):
            grid[i][4-i] = sym if random.randint(0, 1) else grid[i][4-i]
        sym = random_symbol()
        for pos in [(0,0),(4,4),(0,4),(4,0),(2,2)]:
            c,r = pos
            grid[c][r] = sym if random.randint(0, 1) else grid[c][r]
        sym = random_symbol()
        for pos in [(0,0),(4,4),(4,0),(0,4)]:
            c,r = pos
            grid[c][r] = sym if random.randint(0,1) else grid[c][r]
        sym = random_symbol()
        borda_positions = [
            (0,0),(1,0),(2,0),(3,0),(4,0),
            (0,4),(1,4),(2,4),(3,4),(4,4),
            (0,1),(0,2),(0,3),
            (4,1),(4,2),(4,3)
        ]
        for c,r in borda_positions:
            grid[c][r] = sym if random.randint(0,1) else grid[c][r]
        sym = random_symbol()
        for c in range(5):
            for r in range(5):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]

    elif LEVEL == 2:
        for c in range(5):
            sym = random_symbol()
            for r in range(5):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]
        for r in range(5):
            sym = random_symbol()
            for c in range(5):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]
    elif LEVEL == 3:
        for c in range(5):
            sym = random_symbol()
            for r in range(5):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]

    return grid

# -----------------------------
# checkWins 
# -----------------------------
def check_wins(grid):
    wins = []

    def addWin(type_, positions):
        multiplier = 0
        if type_ == "horizontal": multiplier = 5
        elif type_ == "vertical": multiplier = 8
        elif type_ in ("diagonal_principal", "diagonal_invertida"): multiplier = 12
        elif type_ == "cruzado_x": multiplier = 20
        elif type_ == "janela": multiplier = 15
        elif type_ == "janelao": multiplier = 30
        elif type_ == "cheio": multiplier = 50

        wins.append({
            "type": type_,
            "positions": positions,
            "payout": multiplier
        })

    # horizontais
    for r in range(5):
        if all(grid[c][r] == grid[0][r] for c in range(5)):
            addWin("horizontal", [(c, r) for c in range(5)])

    # verticais
    for c in range(5):
        if all(grid[c][r] == grid[c][0] for r in range(5)):
            addWin("vertical", [(c, r) for r in range(5)])

    # diagonal principal
    if all(grid[i][i] == grid[0][0] for i in range(5)):
        addWin("diagonal_principal", [(i, i) for i in range(5)])

    # diagonal invertida
    if all(grid[i][4 - i] == grid[0][4] for i in range(5)):
        addWin("diagonal_invertida", [(i, 4 - i) for i in range(5)])

    # cruzado X
    if (
        grid[0][0] == grid[4][4] and
        grid[0][4] == grid[4][0] and
        grid[0][0] == grid[2][2] and
        grid[0][0] == grid[0][4]
    ):
        addWin("cruzado_x", [(0,0),(4,4),(0,4),(4,0),(2,2)])

    # janela
    if (
        grid[0][0] == grid[4][4] and
        grid[4][0] == grid[0][4] and
        grid[0][0] == grid[4][0]
    ):
        addWin("janela", [
            (0,0),(4,4),(4,0),(0,4)
        ])

    # borda / janelao
    borda_positions = [
        (0,0),(1,0),(2,0),(3,0),(4,0),
        (0,4),(1,4),(2,4),(3,4),(4,4),
        (0,1),(0,2),(0,3),
        (4,1),(4,2),(4,3)
    ]
    borda = [grid[c][r] for (c,r) in borda_positions]
    if all(s == borda[0] for s in borda):
        addWin("janelao", borda_positions)

    # cheio
    full_positions = [(c,r) for c in range(5) for r in range(5)]
    flat = [grid[c][r] for (c,r) in full_positions]
    if all(s == flat[0] for s in flat):
        addWin("cheio", full_positions)

    return wins

# Helper: normalize digits
def only_digits(s):
    return re.sub(r'\D', '', s or "")

@app.route("/rodar/<string:user_id>", methods=["POST"])
def rodar(user_id):
    user = user_model.get_user_by_id(user_id)
    
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    user_balance = float(user.get("balance", 0.0))

    bet_raw = request.json.get("bet") if request.json else 0.5
    try:
        bet = max(0.01, float(bet_raw))
    except:
        bet = 0.5

    if user_balance < bet:
        return jsonify({"error": "Saldo insuficiente"}), 400

    grid = generate_grid()
    wins = check_wins(grid)
    total_win = bet * len(wins) * 10.0 if wins else 0.0

    if total_win > 0:
        new_balance = user_balance + total_win
        machine.balance -= total_win
    else:
        new_balance = user_balance - bet
        machine.balance += bet

    user_model.update_user(user_id, {"balance": float(new_balance)})

    return jsonify({
        "grid": grid,
        "win": round(total_win, 2),
        "balance_user": round(new_balance, 2),
        "balance_machine": round(machine.balance, 2),
        "wins": wins,
        "level": LEVEL
    })

#==========================================================================================
# CRIAR REGISTRO DOS USER 
#==========================================================================================
@app.route("/users", methods=["POST"])
def register_user():
    data = request.get_json()
    required = ["nome","sobrenome","cpf","data_nascimento","email","senha"]
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
        "cpf": cpf_digits,
        "data_nascimento": data["data_nascimento"],
        "email": data["email"],
        "convite_ganbista": data.get("convite_ganbista",""),
        "chave_pix": data.get("chave_pix",""),
        "senha": data["senha"],
        "balance": 50.0,  # inicial para o user pelo registro
        "created_at": datetime.now()
    }
    user_id = user_model.create_user(new_user)
    return jsonify({"id": user_id}), 201

#========================================
# LOGIN CPF
#========================================
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
        "redirect": f"/acesso/users/{user['_id']}"
    })

#======================================================
# -LOGIN E REGISTRO DOS USERS
#======================================================
@app.route("/")
def index():
    return render_template("index.html")

#======================================================
# -ROTAS COMPRAS NO APP
#======================================================
# @app.route("/compras/<string:user_id>")
# def compras(user_id):
#     return render_template("payments.html")

@app.route("/carrinho/<string:user_id>")
def carrinho(user_id):
    return render_template("carrinho.html")    
#======================================================
# -PAGAMENTO VIA PIX QRCODE
#======================================================
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

@app.route("/compras/pagamento_pix/<string:user_id>")
def compras_pagamento_pix(user_id):
    nome = request.args.get("nome") or ""
    email = request.args.get("email") or ""
    cpf = request.args.get("cpf") or ""
    qtd = request.args.get("qtd") or "0"

    quantity = int(qtd)
    valor_total = quantity * 5.00

    payment_data = {
        "transaction_amount": valor_total,
        "description": "Block Animation",
        "payment_method_id": "pix",
        "payer": {
            "email": email,
            "first_name": nome,
            "identification": {
                "type": "CPF",
                "number": cpf
            }
        },
        "additional_info": {
            "items": [
                {
                    "title": "Bloco Animation",
                    "quantity": quantity,
                    "unit_price": 5.00
                }
            ]
        },
        "external_reference": email
    }

    response = sdk.payment().create(payment_data)
    mp = response.get("response", {})

    if "id" not in mp:
        return f"ERRO NO RETORNO DO MERCADO PAGO:<br><br>{mp}", 500

    payment_id = str(mp["id"])
    status = mp.get("status", "pending")

    documento = criar_documento_pagamento(
        payment_id=payment_id,
        status=status,
        valor=valor_total,
        user_id=user_id,
        email_user=email
    )

    PagamentoModel().create_pagamento(documento)

    transaction = mp["point_of_interaction"]["transaction_data"]
    qrcode_base64 = transaction["qr_code_base64"]
    qrcode_text = transaction["qr_code"]

    return render_template(
        "compras/transaction_pix.html",
        qrcode=f"data:image/png;base64,{qrcode_base64}",
        valor=f"R$ {valor_total:.2f}",
        qr_code_cola=qrcode_text
    )
#========================================
# WEBHOOK MERCADO PAGO
#========================================
@app.route("/notificacoes", methods=["POST"])
def webhook_mp():
    data = request.get_json()
    topic = data.get("topic", data.get("type"))

    if topic == "payment":
        payment_id = data.get("data", {}).get("id")

        if payment_id:
            info = sdk.payment().get(payment_id)

            if info["status"] == 200:
                pag_data = info["response"]
                status = pag_data.get("status")

                pagamentos_collection.update_one(
                    {"_id": str(payment_id)},
                    {"$set": {
                        "status": status,
                        "data_atualizacao": datetime.utcnow(),
                        "detalhes_webhook": pag_data
                    }},
                    upsert=True
                )

                if status == "approved":
                    return redirect("/compra/sucesso")

                if status in ["rejected", "cancelled"]:
                    return redirect("/compra/recusada")

    return jsonify({"status": "ok"}), 200


# @app.route("/compra/sucesso")
# def compra_sucesso():
#     return render_template("compras/sucesso.html")


# @app.route("/compra/recusada")
# def compra_recusada():
#     return render_template("compras/recusada.html") 
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
        balance_value = user.get('balance', 0)

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
# -ROTA MAQUINA 5x5
#==========================================================
@app.route("/acesso/users/<string:user_id>")
def acesso_users_machine(user_id):
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

        return render_template("slotmachine.html", user_id=user_id, balance=balance_value)
    else:
        return "Usuário não encontrado"

#==========================================================
# -ROTA MAQUINA 5x4
#==========================================================
@app.route("/acesso/users/5x4/<string:user_id>")
def acesso_users_machine_5x4(user_id):
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

        return render_template("slotmachine5x4.html", user_id=user_id, balance=balance_value)
    else:
        return "Usuário não encontrado"       

#==========================================================
# -ROTA MAQUINA 3x3
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







#====================================================================================================
# -PLATAFORMA RAFFLES
#=====================================================================================================
@app.route("/compras_rf/<string:user_id>", methods=["POST"])
def compras_rf_user(user_id):
    data = request.get_json()

    # validação
    required_fields = ["tickets", "valor", "quantity", "valor_unit"]
    for field in required_fields:
        if field not in data or not data[field]:
            return jsonify({"error": f"Campo obrigatório: {field}"}), 400

    # pega dados do usuário na collection users
    user = user_model.get_user_by_id(user_id)
    if not user:
        return jsonify({"error": "Usuário não encontrado"}), 404

    cpf = user.get("cpf")
    email_user = user.get("email")

    # monta o registro que vai pro banco
    new_compras_rf = {
        "user_id": user_id,
        "cpf": cpf,
        "email_user": email_user,
        "tickets": data["tickets"],      # vem do frontend
        "valor": data["valor"],          # vem do frontend
        "quantity": data["quantity"],    # vem do frontend
        "valor_unit": data["valor_unit"],# vem do frontend
        "created_at": datetime.now()
    }

    compras_rf_id = compras_rf_model.create_compras_rf(new_compras_rf)

    return jsonify({"id": compras_rf_id}), 201


@app.route("/index/users/<string:user_id>")
def raffle_inicio(user_id):
    return render_template("rifa/index.html", user_id=user_id)

@app.route("/users/produto/<string:user_id>")
def raffle(user_id):
    return render_template("rifa/raffle.html", user_id=user_id)

# @app.route("/raffle/diego/review/users/<string:user_id>")
# def review_raffle(user_id):
# 
#     user = user_model.get_user_by_id(user_id)
#     if user:
#         nome_value = user.get('nome')
#         cpf_value = user.get('cpf')
#         email_value = user.get('email')
# 
# 
#     return render_template("rifa/review.html", user_id=user_id, nome=nome_value, cpf=cpf_value, email=email_value)

@app.route("/raffle/diego/review/users/<string:user_id>")
def review_raffle(user_id):

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
        valor=compra_rf.get("valor_unit"),
        valor_final=compra_rf.get("valor"),
        quantity=compra_rf.get("quantity"),
        tickets=compra_rf.get("tickets", [])
    )
                   


#============================================================
# -PAGAMENTO VIA PIX QRCODE
#===========================================================
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

@app.route("/raffle/pagamento_pix/<string:user_id>")
def pagamento_pix(user_id):
    nome = request.args.get("nome") or ""
    email = request.args.get("email") or ""
    cpf = request.args.get("cpf") or ""
    telefone = request.args.get("telefone") or ""
    qtd = int(request.args.get("qtd") or 0)

    valor_total = qtd * 0.5

    payment_data = {
        "transaction_amount": valor_total,
        "description": "Block Animation",
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
        valor=valor_total,
        user_id=user_id,
        email_user=email
    )

    PagamentoModel().create_pagamento(documento)

    tx = mp["point_of_interaction"]["transaction_data"]

    return render_template(
        "rifa/transaction_pix.html",
        qrcode=f"data:image/png;base64,{tx['qr_code_base64']}",
        valor=f"R$ {valor_total:.2f}",
        qr_code_cola=tx["qr_code"]
    )

#========================================
# -WEBHOOK
#========================================
@app.route("/notificacoes", methods=["POST"])
def webhook_mps():
    data = request.get_json()

    topic = data.get("type") or data.get("topic")
    if topic != "payment":
        return jsonify({"status": "ignored"}), 200

    payment_id = data.get("data", {}).get("id")
    if not payment_id:
        return jsonify({"status": "no payment"}), 200

    info = sdk.payment().get(payment_id)

    if info["status"] != 200:
        return jsonify({"status": "mp error"}), 200

    pag = info["response"]
    status = pag.get("status")
    user_id = pag.get("external_reference")  # ← AQUI VEM O USER_ID

    pagamentos_collection.update_one(
        {"_id": str(payment_id)},
        {"$set": {
            "status": status,
            "user_id": user_id,
            "data_atualizacao": datetime.utcnow(),
            "detalhes_webhook": pag
        }},
        upsert=True
    )

    return jsonify({"status": "ok"}), 200


#------------------------------------------------
# -COMPRA SUCCESS
#------------------------------------------------
# @app.route("/sorteio/<string:user_id>")
# def compra_sucesso_raffle(user_id):
#     # pega o último sorteio
#     sorteio = sorteio_model.collection.find_one({}, sort=[("_id", -1)])
# 
#     # valores do sorteio
#     concurso_value = sorteio.get('concurso') if sorteio else ""
#     data_value = sorteio.get('data') if sorteio else ""
#     dezenas_value = sorteio.get('dezenas') if sorteio else []
# 
#     # pega a compra do usuário
#     compra_rf = compras_rf_model.collection.find_one(
#         {"user_id": user_id},
#         sort=[("_id", -1)]
#     )
# 
#     user = user_model.get_user_by_id(user_id)
#     nome_value = user.get('nome') if user else ""
#     cpf_value = user.get('cpf') if user else ""
#     email_value = user.get('email') if user else ""
# 
#     if not compra_rf:
#         return render_template(
#             "rifa/sorteio.html",
#             user_id=user_id,
#             nome=nome_value,
#             quantity=0,
#             tickets=[],
#             concurso=concurso_value,
#             data=data_value,
#             dezenas=dezenas_value
#         )
# 
#     return render_template(
#         "rifa/sorteio.html",
#         user_id=user_id,
#         nome=nome_value,
#         quantity=compra_rf.get("quantity"),
#         tickets=compra_rf.get("tickets", []),
#         concurso=concurso_value,
#         data=data_value,
#         dezenas=dezenas_value
#     )

@app.route('/compra/sucesso')
def success():
    return render_template("rifa/sorteio.html")
#=================================================================================================
    
#----------------------------------------------------------
# -PAGAMENTO RECUSADO
#----------------------------------------------------------


@app.route("/compra/recusada")
def compra_recusada_raffle():
    return render_template("rifa/recusada.html")


    
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
@app.route("/login_admin/organizadores")
def login_administradores():
    return render_template("rifa/admin_dashboard/login.html")



@app.route("/users/full", methods=["GET"])
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


#===========================================
# -Run
#===========================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

