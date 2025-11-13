# main.py
from flask import Flask, request, jsonify, abort
from model import UsuarioModel
from bson.errors import InvalidId
import os
app = Flask(__name__)
user_model = UsuarioModel()

@app.route('/users', methods=['POST'])
def create_user():
    """Rota para criar um novo usuário."""
    data = request.get_json()
    if not data or 'nome' not in data or 'email' not in data:
        return jsonify({"error": "Dados inválidos fornecidos."}), 400
    
    user_id = user_model.create_user(data)
    return jsonify({"message": "Usuário criado com sucesso", "id": user_id}), 201

@app.route('/users', methods=['GET'])
def get_users():
    """Rota para listar todos os usuários."""
    users = user_model.get_all_users()
    return jsonify(users), 200

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



port = int(os.environ.get("PORT", 8000))
app.run(app, host="0.0.0.0", port=port, log_level="debug")

