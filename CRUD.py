import pymongo
from bson.objectid import ObjectId

client = pymongo.MongoClient("mongodb+srv://Ferrari-games-itech-io:0UgcAgov7VgUCJO3@ferrarigamesitechio.cqes1cf.mongodb.net/?appName=FerrariGamesItechIo")
db = client["FerrariGamesItechIo"]


def listar_collections():
    return db.list_collection_names()


def print_tabela(docs):
    if not docs:
        print("\nNenhum documento encontrado.\n")
        return

    chaves = sorted({k for doc in docs for k in doc.keys()})
    larguras = {k: max(len(str(k)), max(len(str(doc.get(k, ""))) for doc in docs)) for k in chaves}

    linha = " | ".join(k.ljust(larguras[k]) for k in chaves)
    print(linha)
    print("-" * len(linha))

    for doc in docs:
        print(" | ".join(str(doc.get(k, "")).ljust(larguras[k]) for k in chaves))


def converter_tipo(valor_original, novo_valor):
    if isinstance(valor_original, int):
        try:
            return int(novo_valor)
        except:
            return novo_valor
    if isinstance(valor_original, float):
        try:
            return float(novo_valor)
        except:
            return novo_valor
    if isinstance(valor_original, bool):
        return novo_valor.lower() in ("true", "1", "t", "sim")
    return novo_valor


def editar_documento(col, doc_id):
    try:
        oid = ObjectId(doc_id)
    except:
        print("\nID inválido.\n")
        return

    doc = col.find_one({"_id": oid})
    if not doc:
        print("\nDocumento não encontrado.\n")
        return

    print("\n=== EDITAR DOCUMENTO ===")
    for k, v in doc.items():
        print(f"{k}: {v}")

    print("\nDigite apenas ENTER para manter o valor atual.\n")

    novos = {}
    for campo, valor in doc.items():
        if campo == "_id":
            continue

        entrada = input(f"{campo} ({valor}): ").strip()

        if entrada != "":
            novos[campo] = converter_tipo(valor, entrada)

    if novos:
        col.update_one({"_id": oid}, {"$set": novos})
        print("\nDocumento atualizado com sucesso!\n")
    else:
        print("\nNenhuma alteração realizada.\n")


def abrir_collection(nome_col):
    col = db[nome_col]

    docs = list(col.find().limit(50))
    print("\n=== DOCUMENTOS ===\n")
    print_tabela(docs)

    print("\n1 - Editar documento")
    print("0 - Voltar")

    acao = input("\nEscolha: ")

    if acao == "1":
        doc_id = input("ID do documento (_id): ").strip()
        editar_documento(col, doc_id)


def mostrar_menu():
    cols = listar_collections()
    if not cols:
        print("\nNenhuma collection encontrada.\n")
        return

    print("\n=== COLLECTIONS ===")
    for i, nome in enumerate(cols):
        print(f"{i+1} - {nome}")
    print("0 - Sair")

    opcao = input("\nEscolha uma opção: ")

    if opcao == "0":
        exit()

    try:
        idx = int(opcao) - 1
        nome_col = cols[idx]
    except:
        print("Opção inválida.")
        return

    print(f"\nSelecionada: {nome_col}")
    print("1 - Abrir (listar + editar)")
    print("2 - Deletar collection")
    print("0 - Voltar")

    acao = input("\nEscolha a ação: ")

    if acao == "1":
        abrir_collection(nome_col)

    elif acao == "2":
        confirmar = input(f"Digite DELETE para confirmar exclusão de '{nome_col}': ")
        if confirmar == "DELETE":
            db[nome_col].drop()
            print("\nCollection deletada.\n")
        else:
            print("\nCancelado.\n")

    input("\nENTER para continuar...")


while True:
    mostrar_menu()
