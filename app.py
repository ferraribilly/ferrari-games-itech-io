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

class Player:
    def __init__(self, balance=50.0):
        self.balance = float(balance)

class Machine:
    def __init__(self, balance=1000.0):
        self.balance = float(balance)

machine = Machine()
player = Player()

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
        # vertical: repetir símbolo em todas colunas
        for c in range(5):
            sym = random_symbol()
            for r in range(5):
                grid[c][r] = sym if random.randint(0, 1) else grid[c][r]
        # horizontal
        for r in range(5):
            sym = random_symbol()
            for c in range(5):
                grid[c][r] = sym if random.randint(0, 1) else grid[c][r]
        # diagonal principal
        sym = random_symbol()
        for i in range(5):
            grid[i][i] = sym if random.randint(0, 1) else grid[i][i]
        # diagonal invertida
        sym = random_symbol()
        for i in range(5):
            grid[i][4-i] = sym if random.randint(0, 1) else grid[i][4-i]
        # cruzado X
        sym = random_symbol()
        for pos in [(0,0),(4,4),(0,4),(4,0),(2,2)]:
            c,r = pos
            grid[c][r] = sym if random.randint(0, 1) else grid[c][r]
        # janela
        sym = random_symbol()
        for pos in [(0,0),(4,4),(4,0),(0,4)]:
            c,r = pos
            grid[c][r] = sym if random.randint(0,1) else grid[c][r]
        # janelao (borda)
        sym = random_symbol()
        borda_positions = [
            (0,0),(1,0),(2,0),(3,0),(4,0),
            (0,4),(1,4),(2,4),(3,4),(4,4),
            (0,1),(0,2),(0,3),
            (4,1),(4,2),(4,3)
        ]
        for c,r in borda_positions:
            grid[c][r] = sym if random.randint(0,1) else grid[c][r]
        # cheio
        sym = random_symbol()
        for c in range(5):
            for r in range(5):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]

    elif LEVEL == 2:
        # Facilita vertical e horizontal
        for c in range(5):
            sym = random_symbol()
            for r in range(5):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]
        for r in range(5):
            sym = random_symbol()
            for c in range(5):
                grid[c][r] = sym if random.randint(0,1) else grid[c][r]
    elif LEVEL == 3:
        # Facilita apenas vertical
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


@app.route("/rodar", methods=["POST"])
def rodar():
    bet_raw = request.form.get("bet") if request.form else None
    if bet_raw is None:
        data = request.get_json(silent=True) or {}
        bet_raw = data.get("bet", 0.5)

    try:
        bet = float(bet_raw)
    except:
        bet = 0.5

    bet = max(0.01, bet)

    grid = generate_grid()
    wins = check_wins(grid)

    total_win = 0.0
    if len(wins) > 0:
        total_win = bet * len(wins) * 10.0

    if total_win > 0:
        player.balance += total_win
        machine.balance -= total_win
    else:
        player.balance -= bet
        machine.balance += bet

    return jsonify({
        "grid": grid,
        "win": round(total_win, 2),
        "balance_player": round(player.balance, 2),
        "balance_machine": round(machine.balance, 2),
        "wins": wins,
        "level": LEVEL
    })






#===========================
# CRIAR USUÁRIO
#===========================
@app.route('/users', methods=['POST'])
def create_user():
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


@app.route('/users', methods=['GET'])
def get_users():
    users = user_model.get_all_users()
    return jsonify(users), 200


@app.route('/users/<string:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        user = user_model.get_user_by_id(user_id)
        if user:
            return jsonify(user), 200
        return jsonify({"error": "Usuário não encontrado."}), 404
    except InvalidId:
        return jsonify({"error": "ID inválido."}), 400


@app.route('/users/<string:user_id>', methods=['PUT'])
def update_user_route(user_id):
    data = request.get_json()
    if not data:
        return jsonify({"error": "Nenhum dado fornecido."}), 400

    try:
        modified = user_model.update_user(user_id, data)
        if modified:
            return jsonify({"message": "Usuário atualizado."}), 200
        return jsonify({"error": "Usuário não encontrado."}), 404
    except InvalidId:
        return jsonify({"error": "ID inválido."}), 400


@app.route('/users/<string:user_id>', methods=['DELETE'])
def delete_user_route(user_id):
    try:
        deleted = user_model.delete_user(user_id)
        if deleted:
            return jsonify({"message": "Usuário excluído."}), 200
        return jsonify({"error": "Usuário não encontrado."}), 404
    except InvalidId:
        return jsonify({"error": "ID inválido."}), 400



#========================================
# LOGIN CPF
#========================================
def only_digits(s):
    return re.sub(r'\D', '', s or "")

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or 'cpf' not in data:
        return jsonify({"error": "CPF obrigatório."}), 400

    input_cpf = only_digits(data["cpf"])

    users = user_model.get_all_users()
    for user in users:
        user_cpf = only_digits(user.get("cpf", ""))
        if user_cpf == input_cpf and user.get("_id"):
            return jsonify({"redirect": f"/loading/users/{user['_id']}"}), 200

    return jsonify({"error": "CPF não encontrado."}), 404



#========================================
# CRIAR PAGAMENTO
#========================================
@app.route("/criar-pagamento/users/<string:user_id>", methods=["POST"])
def criar_pagamento(user_id):
    data = request.get_json()
    titulo = data.get("titulo")
    valor = data.get("valor")
    email_user = data.get("email")

    if not titulo or not valor or not email_user:
        return jsonify({"erro": "Dados insuficientes"}), 400

    preference_data = {
        "items": [
            {"title": titulo, "quantity": 1, "unit_price": float(valor)}
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

    pagamento_doc = criar_documento_pagamento(
        payment_id=preference["id"],
        status="pending",
        valor=float(valor),
        user_id=user_id,
        email_user=email_user
    )

    pagamentos_collection.insert_one(pagamento_doc)

    return jsonify({
        "id_preferencia": preference["id"],
        "link_pagamento": preference["init_point"]
    })



#========================================
# CRUD COMPLETO DE PAGAMENTOS
#========================================
@app.route("/pagamentos", methods=["GET"])
def listar_pagamentos():
    pagamentos = pagamento_model.get_all_pagamentos()
    return jsonify(pagamentos), 200


@app.route("/pagamentos/<string:pag_id>", methods=["GET"])
def obter_pagamento(pag_id):
    pagamento = pagamento_model.get_pagamento(pag_id)
    if pagamento:
        return jsonify(pagamento), 200
    return jsonify({"error": "Pagamento não encontrado."}), 404


@app.route("/pagamentos/<string:pag_id>", methods=["PUT"])
def atualizar_pagamento(pag_id):
    data = request.get_json()
    modified = pagamento_model.update_pagamento(pag_id, data)
    if modified:
        return jsonify({"message": "Pagamento atualizado."}), 200
    return jsonify({"error": "Não encontrado."}), 404


@app.route("/pagamentos/<string:pag_id>", methods=["DELETE"])
def deletar_pagamento(pag_id):
    deleted = pagamento_model.delete_pagamento(pag_id)
    if deleted:
        return jsonify({"message": "Pagamento removido."}), 200
    return jsonify({"error": "Não encontrado."}), 404



#========================================
# CRUD BALANCE
#========================================
@app.route("/balance", methods=["GET"])
def listar_balance():
    balances = balance_model.get_all_balances()
    return jsonify(balances), 200


@app.route("/balance/<string:user_id>", methods=["GET"])
def obter_balance(user_id):
    bal = balance_model.get_balance_by_user(user_id)
    if bal:
        return jsonify(bal), 200
    return jsonify({"error": "Balance não encontrado."}), 404


@app.route("/balance/<string:user_id>", methods=["PUT"])
def atualizar_balance(user_id):
    data = request.get_json()
    modified = balance_model.update_balance(user_id, data)
    if modified:
        return jsonify({"message": "Balance atualizado."}), 200
    return jsonify({"error": "Não encontrado."}), 404


@app.route("/balance/<string:user_id>", methods=["DELETE"])
def deletar_balance(user_id):
    deleted = balance_model.delete_balance(user_id)
    if deleted:
        return jsonify({"message": "Balance removido."}), 200
    return jsonify({"error": "Não encontrado."}), 404



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
                    {"_id": payment_id},
                    {"$set": {
                        "status": status,
                        "data_atualizacao": datetime.utcnow(),
                        "detalhes_webhook": pag_data
                    }},
                    upsert=True
                )

                if status == "approved":
                    valor = pag_data.get("transaction_amount", 0)
                    user_id = pagamentos_collection.find_one({"_id": payment_id}).get("user_id")

                    criar_balance(
                        user_id=user_id,
                        valor=valor
                    )

    return jsonify({"status": "ok"}), 200



#========================================
# TEMPLATES
#========================================
@app.route('/')
def criar_user():
    return render_template('index.html')

@app.route('/loading/users/<string:user_id>')
def loading(user_id):
    return render_template('carregando.html')


@app.route('/painel/users/<string:user_id>')
def user_profile(user_id):
    return render_template('painel_game.html')


@app.route('/compras/users/')
def compras():
    return render_template('compras.html')

@app.route('/pending')
def pending():
    return render_template('pending.html')

@app.route('/failure')
def failure():
    return render_template('failure.html')

@app.route('/jogo_bicho')
def jogo_bicho():
    return render_template('jogo_bicho.html')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
