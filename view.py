from flask import Blueprint, render_template, request, redirect, url_for
from datetime import datetime, timezone, timedelta
from model import Usuario
from model import get_db_status
import re
import random
from loteria_caixa import Federal
from collections import defaultdict
import os
from requests import get, ConnectionError
from functools import lru_cache
from urllib3 import disable_warnings, exceptions

main_bp = Blueprint('main', __name__)


@main_bp.route('/status_conexao', methods=['GET'])
def status_conexao():
    """
    Rota para testar a conexão com o MongoDB.
    """
    if get_db_status():
        return jsonify(
            {
                "status": "OK",
                "database_connection": "Successful"
            }
        ), 200
    else:
        return jsonify(
            {
                "status": "Error",
                "database_connection": "Failed"
            }
        ), 500


@main_bp.route('/teste')
def home():
    return "Aplicação Flask em execução. Use a rota /status_conexao para testar o MongoDB."
        
# -----------------------
# Helpers
# -----------------------
def calcular_idade(data_nascimento):
    hoje = date.today()
    return hoje.year - data_nascimento.year - ((hoje.month, hoje.day) < (data_nascimento.month, data_nascimento.day))

def validar_cpf(cpf_raw):
    if not cpf_raw:
        return False
    cpf = re.sub(r'\D', '', cpf_raw)
    return len(cpf) == 11

# -----------------------
# Rotas
# -----------------------


@main_bp.route('/registrar_usuario', methods=['POST'])
def adicionar_usuario():
    data = request.get_json() or request.form

    nome = data.get('nome')
    sobrenome = data.get('sobrenome')
    email = data.get('email')
    cpf = data.get('cpf')
    chave_pix = data.get('chave_pix')
    convite_ganbista = data.get('convite_ganbista') or data.get('public_key_admin')
    senha = data.get('senha')
    data_nascimento_str = data.get('data_nascimento')

    if not all([nome, sobrenome, email, cpf, chave_pix, convite_ganbista, senha, data_nascimento_str]):
        return jsonify({"status": "error", "message": "Todos os campos são obrigatórios!"}), 400

    if not validar_cpf(cpf):
        return jsonify({"status": "error", "message": "CPF inválido (deve conter 11 dígitos)."}), 400

    try:
        data_nascimento = datetime.strptime(data_nascimento_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"status": "error", "message": "Data de nascimento inválida! Use YYYY-MM-DD."}), 400

    idade = calcular_idade(data_nascimento)
    if idade < 18:
        return redirect(url_for('main.proibido'))

    cpf_limpo = re.sub(r'\D', '', cpf)
    usuario_existente = Usuario.find_by_cpf(cpf_limpo)
    if usuario_existente:
        return jsonify({"status": "error", "message": "Este CPF já está cadastrado!"}), 400

    novo_usuario = Usuario(nome, sobrenome, cpf_limpo, data_nascimento, email, chave_pix, convite_ganbista, senha)
    usuario_id = novo_usuario.save()
    session['user_id'] = str(usuario_id)

    return jsonify({"status": "success", "message": "Usuário registrado com sucesso!"})

@main_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or request.form
    cpf = data.get('cpf')
    if not cpf:
        return jsonify({"status": "error", "message": "Informe o CPF!"}), 400

    cpf_limpo = re.sub(r'\D', '', cpf)
    usuario = Usuario.find_by_cpf(cpf_limpo)
    if not usuario:
        return jsonify({"status": "error", "message": "CPF não encontrado! Faça o cadastro primeiro."}), 400

    session['user_id'] = str(usuario['_id'])
    return jsonify({"status": "success", "message": f"Bem-vindo {usuario['nome']}!", "redirect": url_for('main.painel')})


@main_bp.route('/loading')
def loading():
    return render_template('jogo_bixo/loading.html')

@main_bp.route("/painel", methods=['GET'])
def painel():
     return render_template("jogo_bixo/painel_game.html")



@main_bp.route('/regras')
def regras():
    return render_template('regulamento.html')

@main_bp.route('/')
def index():
   #  usuarios = Usuario.find_all()  # substitui Usuario.query.all()
    return render_template('jogo_bixo/registro.html')

@main_bp.route('/proibido')
def proibido():
    return render_template('proibido.html')

@main_bp.route('/jogo_bicho')
def game():
    return render_template('jogo_bixo/jogo_bicho.html')
    

@main_bp.route('/slot')
def slotmachine():
    return render_template('jogo_bixo/slotmachine.html')

@main_bp.route('/pending')
def pending():
    return render_template('jogo_bixo/pending.html')

@main_bp.route('/success')
def success():
    return render_template('jogo_bixo/pending.html')

@main_bp.route('/cotacao')
def cotacoes():
    return render_template('jogo_bixo/cotacoes.html')




# ===============================
# -SlotMachine Jogo Bicho
# ===============================
ANIMAIS = {
    "Avestruz": [1, 2, 3, 4],
    "Águia": [5, 6, 7, 8],
    "Burro": [9, 10, 11, 12],
    "Borboleta": [13, 14, 15, 16],
    "Cachorro": [17, 18, 19, 20],
    "Cabra": [21, 22, 23, 24],
    "Carneiro": [25, 26, 27, 28],
    "Camelo": [29, 30, 31, 32],
    "Cobra": [33, 34, 35, 36],
    "Coelho": [37, 38, 39, 40],
    "Cavalo": [41, 42, 43, 44],
    "Elefante": [45, 46, 47, 48],
    "Galo": [49, 50, 51, 52],
    "Gato": [53, 54, 55, 56],
    "Jacaré": [57, 58, 59, 60],
    "Leao": [61, 62, 63, 64],
    "Macaco": [65, 66, 67, 68],
    "Porco": [69, 70, 71, 72],
    "Pavão": [73, 74, 75, 76],
    "Peru": [77, 78, 79, 80],
    "Touro": [81, 82, 83, 84],
    "Tigre": [85, 86, 87, 88],
    "Urso": [89, 90, 91, 92],
    "Veado": [93, 94, 95, 96],
    "Vaca": [97, 98, 99, 00]
}


# ================================= #
# -Girar Reels 0 a 24 reels
# ================================= #
def girar_slot():
    # Em um slot do bicho, o resultado final é geralmente baseado em dezenas.
    # Podemos sortear uma dezena de 00 a 99.
    dezena_sorteada = random.randint(0, 99)
    # Formata para sempre ter dois dígitos (ex: 05, 99)
    dezena_formatada = f"{dezena_sorteada:02d}"
    return dezena_formatada


def determinar_animal(dezena_sorteada):
    for animal, dezenas in ANIMAIS.items():
        # Converte a dezena sorteada para int para comparação
        if int(dezena_sorteada) in dezenas:
            return animal
    return "Animal não encontrado" # Caso improvável se o mapeamento estiver correto




# =========================
# FAZER APOSTA 
# =========================
@main_bp.route('/apostar', methods=['POST'])
def apostar():
    data = request.json
    tipo = data.get('tipo')
    modo = data.get('modo')
    valor = float(data.get('valor', 0))
    nome = data.get('nome')
    numeros_bicho = data.get('numeros')

    if valor <= 0:
        return jsonify({"error": "Valor inválido"}), 400        

    milhar_sorteado = sortear_milhar()
    retorno, status = calcular_retorno(tipo, valor, numeros_bicho, [milhar_sorteado])
    resultado = obter_grupo_animal(milhar_sorteado)             

    aposta = {
        "nome": nome,
        "valor": valor,
        "tipo": tipo,
        "modo": modo,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),   
        "milhar_sorteado": milhar_sorteado,
        "resultado_animal": resultado[0],
        "retorno": round(retorno, 2),
        "status": status
    }

    minhas_apostas.append(aposta)
    return jsonify(aposta)

# ============================== #
# Dicionário de animais e limite
# ============================== #

# ================================
bichos = [
    "Avestruz","Aguia","Burro","Borboleta","Cachorro","Cabra","Carneiro","Camelo",
    "Cobra","Coelho","Cavalo","Elefante","Galo","Gato","Jacare","Leao","Macaco",
    "Porco","Pavao","Peru","Touro","Tigre","Urso","Veado","Vaca"
]
# ===================================
# ANALISAR BILHETES DE TODOS USUARIOS
# ===================================
def analisar_bilhete(bilhete):
    milhar = bilhete[:4]
    centena = bilhete[2:]
    dezena = int(bilhete[-2:])
    if dezena == 0:
        dezena = 100
    indice_bicho = (dezena - 1) // 4
    bicho = bichos[indice_bicho]
    grupo = indice_bicho + 1
    return milhar, centena, dezena, bicho, grupo
# ================================================== #
# RESULTADO FEDERAL TODAS QUARTAS E SABADOS
# ===================≈======================-------- #

@main_bp.route("/resultados/federal")
def resultado_html():
    loteria = Federal()
    bilhetes = loteria.listaDezenas()
    mapa_bichos = defaultdict(list)
    resultados = []

    for i, bilhete in enumerate(bilhetes, start=1):
        milhar, centena, dezena, bicho, grupo = analisar_bilhete(bilhete)
        mapa_bichos[bicho].append(bilhete)
        resultados.append({
            "posicao": i,
            "bilhete": bilhete,
            "milhar": milhar,
            "centena": centena,
            "dezena": dezena,
            "bicho": bicho,
            "grupo": grupo,
            "imagem": url_for('static', filename=f'bichos/{bicho.lower()}.jpg')
        })

    mapa_final = {}
    for bicho_nome in bichos:
        bilhetes_bicho = mapa_bichos.get(bicho_nome, [])
        if bilhetes_bicho:
            mapa_final[bicho_nome] = {
                "grupo": bichos.index(bicho_nome) + 1,
                "bilhetes": bilhetes_bicho,
                "total": len(bilhetes_bicho),
                "imagem": url_for('static', filename=f'bichos/{bicho_nome.lower()}.jpg')
            }

    def proximo_sorteio():
        hoje = datetime.now()
        dia_semana = hoje.weekday()
        if dia_semana < 2:
            prox = hoje + timedelta(days=(2 - dia_semana))
        elif dia_semana < 5:
            prox = hoje + timedelta(days=(5 - dia_semana))
        else:
            prox = hoje + timedelta(days=(9 - dia_semana) % 7)
        return prox.replace(hour=19, minute=0, second=0)

    proxima_data_dt = proximo_sorteio()
    proxima_data = proxima_data_dt.strftime("%d/%m/%Y (quarta ou sábado às 19:00)")

    try:
        concurso_atual = int(loteria.numero())
        proximo_concurso = concurso_atual + 1
    except ValueError:
        concurso_atual = loteria.numero()
        proximo_concurso = "Indisponível"

    template = """
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1, user-scalable=no">
        <title>Jogo do Bicho - Resultado Loteria Federal</title>
        <style>
            * {
                box-sizing: border-box;
            }
            html, body {
                margin: 0;
                padding: 0;
                width: 100%;
                overflow-x: hidden; /* <<< remove rolagem lateral */
                font-family: Arial, sans-serif;
                background: url("https://res.cloudinary.com/dptprh0xk/image/upload/v1762733060/estilo-de-vida-fotorrealista-cassino_hny2za.jpg") center/cover no-repeat;    
                color: #f5f5f5;
            }
            header {
                background: trasnparent;
                color: white;
                text-align: center;
                padding: 20px;
                
            }
            header img {
                max-height: 60px;
                margin-bottom: 10px;
                border-radius:100%;
                border:1px solid blue;
            }
            h1 {
                margin: 0;
                font-size: 2em;
            }

            h2 {
                text-aling: center;
                color: gold;
            }
            
            .typing-effect {
              font-family: monospace;
              color: blue;
              text-align: center;
              white-space: nowrap;
              overflow: hidden;
              border-right: .15em solid orange;
              width: 0;
              animation: typing 3.5s steps(30, end) forwards, blinking .75s step-end infinite;
            }
            @keyframes typing { from { width: 0 } to { width: 100% } }
            @keyframes blinking { from, to { border-color: transparent } 50% { border-color: orange } }
            
            .container {
                padding: 15px;
                max-width: 100%;
                overflow-x: hidden;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
                word-wrap: break-word;
            }
            th, td {
                border: 1px solid #333;
                padding: 6px;
                text-align: center;
                white-space: normal;
                overflow-wrap: break-word;
            }
            th {
                background-color: #00FFAA;
                color: #121212;
            }
            tr:nth-child(even) {
                background-color: #1E1E1E;
            }
            tr:hover {
                background-color: #333;
            }
            .bicho-section {
                margin-top: 20px;
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 10px;
            }
            .bicho-card {
               /* background: #1E1E1E;*/
                backgornd: trasnparent;
                border: 1px solid #333;
                border-radius: 10px;
                padding: 10px;
                width: 140px;
                text-align: center;
                box-shadow: 0 0 10px rgba(0,255,170,0.3);
            }
            .bicho-card img {
                width: 70px;
                height: 70px;
                object-fit: contain;
                margin-bottom: 5px;
            }

            /* --- MOBILE --- */
            @media screen and (max-width: 600px) {
                body {
                    overflow-x: hidden;
                }
                table, th, td {
                    font-size: 11px;
                    padding: 4px;
                }
                .bicho-card {
                    width: 100px;
                    padding: 6px;
                }
                .bicho-card img {
                    width: 50px;
                    height: 50px;
                }
                header h1 {
                    font-size: 1.4em;
                }
                header p, a {
                    font-size: 0.9em;
                }
            }
        </style>
        <script>
            setTimeout(() => { window.location.reload(); }, 60000);
        </script>
    </head>
    <body>
        <header>
            <img src="{{ url_for('static', filename='9226104.jpg') }}" alt="Logo Jogo do Bicho">
            <h1 class="typing-effect">Resultado do Jogo do Bicho</h1>
            <p>Concurso atual: {{ concurso }} | Data do Sorteio: {{ data_sorteio }}</p>
            <p><strong>Próximo concurso:</strong> {{ proximo_concurso }} | <strong>Data:</strong> {{ proxima_data }}</p>
            <a href="/jogo_bicho" style="color:#00FFAA;">Voltar Jogos</a>
        </header>
        <div class="container">
            <h2 class="typing-effect">Bilhetes Premiados</h2>
            <table>
                <tr>
                    <th>Posição</th>
                    <th>Bilhete</th>
                    <th>Milhar</th>
                    <th>Centena</th>
                    <th>Dezena</th>
                    <th>Bicho</th>
                    <th>Grupo</th>
                    <th>Imagem</th>
                </tr>
                {% for r in resultados %}
                <tr>
                    <td>{{ r.posicao }}º</td>
                    <td>{{ r.bilhete }}</td>
                    <td>{{ r.milhar }}</td>
                    <td>{{ r.centena }}</td>
                    <td>{{ r.dezena }}</td>
                    <td>{{ r.bicho }}</td>
                    <td>{{ r.grupo }}</td>
                    <td><img src="{{ r.imagem }}" alt="{{ r.bicho }}" style="max-width:40px;max-height:40px;"></td>
                </tr>
                {% endfor %}
            </table>

            <h2 class="typing-effect">Mapa Completo por Bicho</h2>
            <div class="bicho-section">
                {% for b, info in mapa_bichos.items() %}
                <div class="bicho-card">
                    <img src="{{ info.imagem }}" alt="{{ b }}">
                    <strong>{{ b }} (Grupo {{ info.grupo }})</strong>
                    <p>Bilhetes: {{ info.bilhetes | join(', ') }}</p>
                    <p>Total: {{ info.total }}</p>
                </div>
                {% endfor %}
            </div>
        </div>
    </body>
    </html>
    """

    return render_template_string(
        template,
        concurso=loteria.numero(),
        data_sorteio=loteria.dataApuracao(),
        resultados=resultados,
        mapa_bichos=mapa_final,
        proxima_data=proxima_data,
        proximo_concurso=proximo_concurso
    )





# =================================================================== #
# -Rotas Relacionadas a funcoes de apostas e sorteios
# =================================================================== #
@main_bp.route('/loteria-federal')
def loteria_federal():
    return render_template("loteria_federal.html")

disable_warnings(exceptions.InsecureRequestWarning)

@lru_cache()
class Loterias:
    __headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'pt-br, en;q=0.9,*;q=0.8',
        'DNT': '1',
        'Connection': 'close'
    }

    _MODALIDADES_LOTERICAS = sorted([
        'federal', 'diadesorte', 'duplasena', 'megasena',
        'loteca', 'lotofacil', 'lotomania', 'quina', 'supersete', 'timemania'
    ])

    def __init__(self, modalidade: str, concurso: str | int = ''):
        self.modalidade = modalidade.lower().strip()
        self.concurso = str(concurso)

    def _todos_os_dados(self):
        if self.modalidade not in Loterias._MODALIDADES_LOTERICAS:
            raise ValueError(f"Erro: modalidade '{self.modalidade}' não existe.")
        try:
            url = f"https://servicebus2.caixa.gov.br/portaldeloterias/api/{self.modalidade}/{self.concurso}"
            resposta = get(url, verify=False, headers=Loterias.__headers)
        except ConnectionError:
            raise ConnectionError('Sem conexão com a internet!')
        except:
            raise Exception('Erro ao acessar a API da Caixa.')
        return resposta.json()
@main_bp.route('/resultados/todas/loterias', methods=['GET'])
def resultados_html():
    concurso = request.args.get('concurso', default='')
    resultados = {}
    for modalidade in Loterias._MODALIDADES_LOTERICAS:
        try:
            jogo = Loterias(modalidade, concurso)
            dados = jogo._todos_os_dados()
            resultados[modalidade] = dados
        except Exception as e:
            resultados[modalidade] = {'erro': str(e)}
    return render_template_string(HTML_TEMPLATE, resultados=resultados)

# =====================================
# TABELA RESULTADOS
#=====================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Resultados Loterias</title>
<style>
body { font-family: Arial,sans-serif; background:#f5f5f5; margin:0; padding:0; }
.container { max-width: 1000px; margin:auto; padding:20px; }
h1 { text-align:center; margin-bottom:20px; }
table { width:100%; border-collapse:collapse; background:#fff; }
th, td { border:1px solid #ddd; padding:8px; text-align:center; }
th { background:#4CAF50; color:white; }
tr:nth-child(even) { background:#f2f2f2; }
@media (max-width:600px){
    table, thead, tbody, th, td, tr { display:block; }
    th { position:sticky; top:0; background:#4CAF50; }
    td { text-align:right; padding-left:50%; position:relative; }
    td::before { content: attr(data-label); position:absolute; left:0; width:45%; padding-left:10px; font-weight:bold; text-align:left; }
}
</style>
</head>
<body>
<div class="container">
<h1>Resultados das Loterias</h1>
{% for modalidade, dados in resultados.items() %}
    <h2>{{ modalidade.upper() }}</h2>
    {% if dados.erro %}
        <p style="color:red;">Erro: {{ dados.erro }}</p>
    {% else %}
    <table>
        <thead>
            <tr>
                <th>Concurso</th>
                <th>Data</th>
                {% for i in range(1, 11) %}
                    <th>Dezena {{ i }}</th>
                {% endfor %}
            </tr>
        </thead>
        <tbody>
            <tr>
                <td data-label="Concurso">{{ dados.numero }}</td>
                <td data-label="Data">{{ dados.dataApuracao }}</td>
                {% set dezenas = dados.dezenasSorteadasOrdemSorteio or [] %}
                {% for i in range(10) %}
                    <td data-label="Dezena {{ i+1 }}">{{ dezenas[i] if i < dezenas|length else '-' }}</td>
                {% endfor %}
            </tr>
        </tbody>
    </table>
    {% endif %}
{% endfor %}
</div>
</body>
</html>
"""
