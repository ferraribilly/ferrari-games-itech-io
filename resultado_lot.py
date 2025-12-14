import requests
from model import SorteioModel
import json

def get_dia_de_sorte_results():
    api_url = "https://loteriascaixa-api.herokuapp.com/api/diadesorte/latest"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def salvar_sorteio(model):
    resultado = get_dia_de_sorte_results()
    if "error" in resultado:
        return resultado

    # campos que você quer tratar
    data = {
        "concurso": resultado.get("concurso"),
        "proximoConcurso": resultado.get("proximoConcurso"),
        "data": resultado.get("data"),
        "dataProximoConcurso": resultado.get("dataProximoConcurso"),
        "dezenas": resultado.get("dezenas"),
        "dezenasOrdemSorteio": resultado.get("dezenasOrdemSorteio")
    }

    novo_id = model.create_sorteio(data)
    data["_id"] = novo_id

    return {"status": "ok", "id": novo_id, "salvo": data}

if __name__ == "__main__":
    model = SorteioModel()
    print(json.dumps(salvar_sorteio(model), indent=4, ensure_ascii=False))
