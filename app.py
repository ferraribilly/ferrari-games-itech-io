from flask import Flask, request, jsonify, render_template, redirect, session
from flask_socketio import SocketIO, join_room, emit
import requests
import mercadopago
from io import BytesIO
import base64
import qrcode
import fitz
import re
import os
import pytesseract
from PIL import Image
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import cloudinary
import cloudinary.uploader
from bson.objectid import ObjectId
from models import criar_usuario, users_collection, pagamentos_collection, criar_documento_pagamento, PagamentoModel
from flask_cors import CORS
from datetime import datetime, timezone
import uuid


load_dotenv()

app = Flask(__name__)
CORS(app)
# ---------------- MONGODB ----------------
client = MongoClient(os.getenv("MONGO_URI"))
db = client["rifa"]
colecao = db["participantes"]
pagamento_model = PagamentoModel()
socketio = SocketIO(app, cors_allowed_origins="*")
app.secret_key = os.getenv("APP_SECRET_KEY")  
chave_pix = os.getenv("CHAVE_PIX")
qrCode = os.getenv("QR_CODE")
premiacao1 = os.getenv("PREMIACAO1")
dt_sort = os.getenv("SORTEIO")

# ---------------- CLOUDINARY ----------------
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)


# Rota para registrar usuário
@app.route("/registrar", methods=["POST"])
def registrar():
    try:
        data = request.json
        usuario = criar_usuario(data["nome"], data["cpf"], data["telefone"])
        return jsonify({"status": "sucesso", "usuario": usuario}), 201
    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 400

# 🔐 LOGIN
@app.route("/login", methods=["POST"])
def login():
    try:
        data = request.json

        cpf = str(data["cpf"]).strip()

        usuario = users_collection.find_one({"cpf": cpf})

        if not usuario:
            return jsonify({"status": "erro", "mensagem": "CPF não encontrado"}), 404

        return jsonify({
            "status": "sucesso",
            "usuario_id": str(usuario["_id"])
        }), 200

    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 400

# registro pagina principal 
@app.route("/")
def registro():
    return render_template("registro.html")

# 🔓 Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/dia_das_maes")
def index():
    usuario_id = request.args.get("id")

    if not usuario_id:
        return redirect("/")

    return render_template("index.html", usuario_id=usuario_id)

        

#
@app.route("/gerar_numero/<id>")
def numeros(id):
    usuario = users_collection.find_one({"_id": ObjectId(id)})

    if not usuario:
        return "Usuário não encontrado", 404

    return render_template(
        "gerar_numero.html",
        premiacao1=premiacao1,
        usuario=usuario,
        usuario_id=id

    )



# extracao de informacoes 
def extrair_texto(pdf_path):
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise RuntimeError(f"Erro ao abrir o PDF: {e}")

    texto_completo = ""
    for pagina in doc:
        conteudo = pagina.get_text("text")

        if not conteudo.strip():
            pix = pagina.get_pixmap()
            imagem_pagina = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            conteudo = pytesseract.image_to_string(imagem_pagina, lang="por")

        texto_completo += conteudo + "\n"

    doc.close()
    return " ".join(texto_completo.split())

def extrair_valor(texto):
    valores = re.findall(r"\d{1,3}(?:\.\d{3})*,\d{2}", texto)
    if valores:
        valores_float = []
        for v in valores:
            try:
                valores_float.append(float(v.replace('.', '').replace(',', '.')))
            except:
                pass
        if valores_float:
            return max(valores_float)
    return 0.0



NOME_DESTINATARIO = os.getenv("NOME_DESTINATARIO")
BANCO_PERMITIDO = os.getenv("BANCO_PERMITIDO")

def validar_comprovante(texto):
    texto = texto.upper()

    nome_ok = NOME_DESTINATARIO.upper() in texto if NOME_DESTINATARIO else False
    banco_ok = BANCO_PERMITIDO.upper() in texto if BANCO_PERMITIDO else False
    cpf_ok = re.search(r"\*{3}\.132\.428-\*{2}", texto)

    valor = extrair_valor(texto)

    return nome_ok, banco_ok, bool(cpf_ok), valor


# 🚩 Aqui está a rota Flask que você pediu
@app.route("/validar_comprovante", methods=["POST"])
def validar_comprovante_route():
    if "file" not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400
    
    file = request.files["file"]
    caminho_pdf = os.path.join("/tmp", file.filename)
    file.save(caminho_pdf)

    try:
        texto = extrair_texto(caminho_pdf)
        nome_ok, banco_ok, cpf_ok, valor = validar_comprovante(texto)

        resultado = {
            "nome_ok": nome_ok,
            "banco_ok": banco_ok,
            "cpf_ok": cpf_ok,
            "valor": f"R$ {valor:.2f}",
            "valido": nome_ok and banco_ok and cpf_ok
        }
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
    finally:
        if os.path.exists(caminho_pdf):
            os.remove(caminho_pdf)



@app.route("/usuarios", methods=["GET"])
def listar_usuarios():
    try:
        usuarios_cursor = users_collection.find()

        usuarios = []
        for u in usuarios_cursor:
            usuarios.append({
                "_id": str(u.get("_id")),
                "nome": u.get("nome", ""),
                "cpf": u.get("cpf", ""),
                "telefone": u.get("telefone", "")
            })

        return jsonify({"status": "sucesso", "usuarios": usuarios}), 200

    except Exception as e:
        print("ERRO /usuarios:", e)  # 👈 MUITO IMPORTANTE PRA DEBUG
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

# Editar PUT
@app.route("/usuarios/<usuario_id>", methods=["PUT"])
def editar_usuario(usuario_id):
    try:
        data = request.json

        update_data = {}

        if "nome" in data:
            update_data["nome"] = data["nome"].strip()

        if "cpf" in data:
            cpf = limpar_cpf(data["cpf"])
            if not validar_cpf(cpf):
                return jsonify({"status": "erro", "mensagem": "CPF inválido"}), 400
            update_data["cpf"] = cpf

        if "telefone" in data:
            update_data["telefone"] = data["telefone"].strip()

        if not update_data:
            return jsonify({"status": "erro", "mensagem": "Nenhum dado para atualizar"}), 400

        result = users_collection.update_one(
            {"_id": ObjectId(usuario_id)},
            {"$set": update_data}
        )

        if result.matched_count == 0:
            return jsonify({"status": "erro", "mensagem": "Usuário não encontrado"}), 404

        return jsonify({"status": "sucesso", "mensagem": "Usuário atualizado"})

    except Exception as e:
        return jsonify({"status": "erro", "mensagem": str(e)}), 400



# RESETAR
@app.route("/resetar_banco", methods=["GET"])
def resetar_banco():
    try:
        confirm = request.args.get("confirm")

        if confirm != "SIM":
            return jsonify({"erro": "Use ?confirm=SIM"}), 400

        users_collection.delete_many({})
        

        return jsonify({
            "status": "sucesso",
            "mensagem": "Dados apagados"
        })

    except Exception as e:
        return jsonify({"erro": str(e)}), 500






#===========================================================              
# -PAGAMENTO VIA SOMENTE PIX QRCODE               
#===========================================================              
MP_ACCESS_TOKEN = os.environ.get("MP_ACCESS_TOKEN")              
sdk = mercadopago.SDK(MP_ACCESS_TOKEN)          
# ===========================================  
# WEBHOOK MERCADO PAGO  
# ===========================================  
@app.route("/notificacoes", methods=["POST"])  
def handle_webhook():  
    data = request.json  
    if not data:  
        return "", 200  
  
    payment_id = None  
  
    if "data" in data and "id" in data["data"]:  
        payment_id = data["data"]["id"]  
    elif "id" in data:  
        payment_id = data["id"]  
  
    if not payment_id:  
        return "", 200  
  
    payment_details = get_payment_details(payment_id)  
    if not payment_details:  
        return "", 200  
  
    status = payment_details.get("status")  
  
    
  
    socketio.emit(  
        "payment_update",  
        {  
            "status": status,  
            "payment_id": str(payment_id)  
        },  
        room=str(payment_id)  
    )  
  
    return "", 200  
  
def get_payment_details(payment_id):
    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
    r = requests.get(url, headers=headers, timeout=10)
    return r.json() if r.status_code == 200 else None  

# ===========================================
# GERAR QR CODE PIX
# ===========================================
from bson.objectid import ObjectId

@app.route("/payment_qrcode_pix/pagamento_pix/<id>")
def pagamento_pix(id):

    usuario_id = id

    nome = request.args.get("nome") or ""
    cpf = request.args.get("cpf") or ""
    telefone = request.args.get("telefone") or ""
    quantidade = int(request.args.get("quantidade") or 0)

    valor_total = quantidade * 1.00

    payment_data = {
        "transaction_amount": float(valor_total),
        "description": "Assinatura Portifolio",
        "payment_method_id": "pix",
        "payer": {
            "email": "teste@teste.com",
            "first_name": nome,
            "identification": {
                "type": "CPF",
                "number": cpf
            }
        },
        "external_reference": usuario_id,
        "notification_url": "https://ferrari-games-itech-io.onrender.com/notificacoes"
    }

    try:
        response = sdk.payment().create(payment_data)
        mp = response.get("response", {})

        print("MP RESPONSE:", mp)

        if "id" not in mp:
            return f"ERRO MP: {mp}", 500

        payment_id = str(mp["id"])
        status = mp.get("status", "pending")

        documento = criar_documento_pagamento(
            payment_id=payment_id,
            status=status,
            description=description,
            valor=valor_total,
            usuario_id=usuario_id,
            telefone_user=telefone
        )

        # 🔥 NÃO deixa quebrar aqui
        try:
            PagamentoModel().create_pagamento(documento)
        except Exception as e:
            print("ERRO AO SALVAR:", e)

        # 🔥 NÃO quebra aqui também
        tx = mp.get("point_of_interaction", {}).get("transaction_data", {})

        qr_base64 = tx.get("qr_code_base64")
        qr_code = tx.get("qr_code")

        if not qr_base64 or not qr_code:
            return f"ERRO QR: {tx}", 500

        return render_template(
            "finalize.html",
            qrcode=f"data:image/png;base64,{qr_base64}",
            valor=f"R$ {valor_total:.2f}",
            qr_code_cola=qr_code,
            status=status,
            payment_id=payment_id,
            usuario_id=usuario_id
        )

    except Exception as e:
        print("ERRO GERAL:", e)
        return f"ERRO GERAL: {str(e)}", 500
    
@socketio.on("join_payment")
def join_payment_room(data):
    join_room(data["payment_id"]) 


# ================================================
# UPLOADS DE IMAGENS PARA CLOUDINARY
# ================================================
@app.route('/api/save-comprovante-pagamento', methods=['POST'])
def save_comprovante_pagamento():
    data = request.get_json()
    comprovante_pagamento = data.get('comprovante')
    if comprovante_pagamento:
        print(f"URL recebida e salva no DB: {comprovante}")
        return jsonify({"message": "URL salva com sucesso"}), 200
    return jsonify({"error": "URL não fornecida"}), 400





# =========================
# CREATE
# =========================
@app.route('/pagamentos', methods=['POST'])
def criar_pagamento():
    try:
        data = request.json

        payment_id = str(uuid.uuid4())

        doc = criar_documento_pagamento(
            payment_id=payment_id,
            status=data.get("status", "pendente"),
            valor=data.get("valor"),
            usuario_id=data.get("usuario_id"),
            telefone_user=data.get("telefone_usuario")
        )

        result = pagamento_model.create_pagamento(doc)

        if result:
            return jsonify({"msg": "Pagamento criado", "id": result}), 201
        else:
            return jsonify({"erro": "Erro ao criar pagamento"}), 400

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# =========================
# READ (1)
# =========================
@app.route('/pagamentos/<pagamento_id>', methods=['GET'])
def get_pagamento(pagamento_id):
    pagamento = pagamento_model.get_pagamento(pagamento_id)

    if pagamento:
        return jsonify(pagamento), 200
    else:
        return jsonify({"erro": "Pagamento não encontrado"}), 404


# =========================
# READ (ALL)
# =========================
@app.route('/pagamentos', methods=['GET'])
def get_all_pagamentos():
    pagamentos = pagamento_model.get_all_pagamentos()
    return jsonify(pagamentos), 200


# =========================
# UPDATE
# =========================
@app.route('/pagamentos/<pagamento_id>', methods=['PUT'])
def update_pagamento(pagamento_id):
    try:
        data = request.json

        updated = pagamento_model.update_pagamento(pagamento_id, data)

        if updated:
            return jsonify({"msg": "Pagamento atualizado"}), 200
        else:
            return jsonify({"erro": "Nada foi atualizado"}), 400

    except Exception as e:
        return jsonify({"erro": str(e)}), 500


# =========================
# DELETE
# =========================
@app.route('/pagamentos/<pagamento_id>', methods=['DELETE'])
def delete_pagamento(pagamento_id):
    deleted = pagamento_model.delete_pagamento(pagamento_id)

    if deleted:
        return jsonify({"msg": "Pagamento deletado"}), 200
    else:
        return jsonify({"erro": "Pagamento não encontrado"}), 404

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


    
