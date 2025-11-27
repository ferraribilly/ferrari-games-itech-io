from flask import Flask, request, jsonify, abort, render_template, redirect, url_for
import mercadopago
from datetime import datetime
from model import UsuarioModel, PagamentoModel, pagamentos_collection, criar_documento_pagamento, BalanceModel, balance_collection, criar_balance
from bson.errors import InvalidId
import os
import re
import json
from bson.objectid import ObjectId
from flask_cors import CORS
import random

app = Flask(__name__)

MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN", "SEU_ACCESS_TOKEN")
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)

user_model = UsuarioModel()
pagamento_model = PagamentoModel()
balance_model = BalanceModel()

os.makedirs('static/images', exist_ok=True)

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

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

# -----------------------------
# GERADOR COM VOLATILIDADE LEVEL
# -----------------------------
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
# checkWins CORRIGIDO COM POSIÇÕES
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

#===========================
# CRIAR
#===========================
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

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/acesso/users/rifas/<string:user_id>")
def acesso_users_rifas(user_id):
    # Busca o usuário pelo ID
    user = user_model.get_user_by_id(user_id)

    if user:
        nome_value = user.get('nome')
        # Renderiza o template HTML passando user_id e nome
        return render_template("rifas_influencers.html", user_id=user_id, nome=nome_value)
    else:
        return "Nenhum usuário encontrado no banco de dados."


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


@app.route('/users', methods=['GET'])
def get_users():
    users = user_model.get_all_users()
    return jsonify(users), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

