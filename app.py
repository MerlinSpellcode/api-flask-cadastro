from flask import Flask, url_for, request
import json
import bson
from bson.objectid import ObjectId
from flask_pymongo import PyMongo
from flask_cors import CORS



"""Start Flask"""
app = Flask(__name__)
CORS(app)


"""Config"""
with open("config.json","r") as fp:
    conf = json.load(fp)

"""MongoDB"""
app.config['MONGO_URI'] = conf["db"]
mongo = PyMongo(app)


@app.route('/')
def index():
    return '''
        hello
    '''


# Endpoint inicial, onde o usuário preencherá os dados dele.
# Ele retornará o ID do contrato e o estado cadastral
# Se esse usuário já fez o cadastro, ele retornará o estado cadastral atual dele, para pular etapas.
# Existem 3 estados cadastrais:
# 1: Criação
# 2: Upload de Imagens
# 3: Aprovação
@app.route('/contrato', methods=['POST'])
def contrato():
    # Checando se os campos obrigatórios foram recebidos.
    print("asdijasidas")
    if ('nome' 
            and 'cpf' 
            and 'email'
            and 'valor_do_emprestimo'
            in request.form):
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        # Verificando se o cadastro já existe
        if mongo.db.contratos.find_one({"_id.cpf": request.form['cpf']}):
            print("IF    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            cadastro = mongo.db.contratos.find_one({"_id.cpf": request.form['cpf']})
            return {"estado_cadastral": cadastro["estado_cadastral"],
                    "id_cadastro": str(cadastro["_id"]["id"])}

        # Se o cadastro não existir, ele irá criar um novo
        else:  
            print("ELSE    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            # Preparando dicionário de campos adicionais
            dados_adicionais = {"renda": request.form['renda'] if 'renda' in request.form else "",
                                "nascimento": request.form['nascimento'] if 'nascimento' in request.form else "",
                                "estado_civil": request.form['estado_civil'] if 'estado_civil' in request.form else "",
                                "endereco": request.form['endereco'] if 'endereco' in request.form else ""}
            print("PASSA AQUI    @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
            # Inserido no banco
            contrato_inserido = mongo.db.contratos.insert_one({"_id": {"id": ObjectId(),'cpf': request.form['cpf']},
                                                "nome": request.form['nome'],
                                                "email": request.form['email'],
                                                "valor_do_emprestimo": request.form['valor_do_emprestimo'],
                                                "dados_adicionais": dados_adicionais,
                                                "estado_cadastral": 1,
                                                "status": "Em Andamento..."})

        return {"estado_cadastral": 1,
                "id_cadastro": str(contrato_inserido.inserted_id)}
    else:
        return 'Campo requerido não preenchido'


# Nesse Endpoint é nescessario do id do contrato para funcionar.
# O Id do contrato é retornado na criação do contrato, para que possa utilizar nesse endpoint
@app.route('/upload/<id_contrato>', methods=['POST'])
def upload(id_contrato):
    if id_contrato and mongo.db.contratos.find_one({"_id.id": ObjectId(id_contrato)}):
        if mongo.db.contratos.find_one({"_id.id": ObjectId(id_contrato)}).get("estado_cadastral") != 2:
            return 'Esse contrato já passou essa etapa ou ainda não concluiu a etapa anterior'
        else:
            if 'cpf' in request.files:
                # Pré criação dos nomes das imagens, para evitar o else
                cpf_image_name = ""
                renda_image_name = ""
                imovel_image_name = ""
                try:
                    # Inserindo a foto do CPF ou CNH no banco
                    print("1    #######################")
                    cpf_image = request.files['cpf']
                    # Aqui vou pegar a extensão da imagem, para poder criar um nome único para ela.
                    cpf_image_type = cpf_image.filename[-5:] if ".jpeg" in cpf_image.filename else cpf_image.filename[-4:]
                    cpf_image_name = id_contrato + "__cpf" + cpf_image_type
                    mongo.save_file(cpf_image_name, cpf_image)
                    print("2    #######################")

                    # Inserindo a foto do Comprovação de Renda no banco
                    if 'renda' in request.files:
                        renda_image = request.files['renda']
                        # Aqui vou pegar a extensão da imagem, para poder criar um nome único para ela.
                        renda_image_type = renda_image.filename[-5:] if ".jpeg" in renda_image.filename else renda_image.filename[-4:]
                        renda_image_name = id_contrato + "__renda" + renda_image_type
                        mongo.save_file(renda_image_name, renda_image)
                    # Inserindo a foto do Imovel no banco
                    if 'imovel' in request.files:
                        imovel_image = request.files['imovel']
                        # Aqui vou pegar a extensão da imagem, para poder criar um nome único para ela.
                        imovel_image_type = imovel_image.filename[-5:] if ".jpeg" in imovel_image.filename else imovel_image.filename[-4:]
                        imovel_image_name = id_contrato + "__imovel" + imovel_image_type
                        mongo.save_file(imovel_image_name, imovel_image)

                    # Atualizado dados no banco
                    mongo.db.contratos.update({"_id.id": ObjectId(id_contrato)}, {
                        "$set": {
                            "estado_cadastral": 3,
                            "status": "Aprovado",
                            "fotos": {"cpf": cpf_image_name,
                                        "renda": renda_image_name,
                                        "imovel": imovel_image_name}
                        }
                    })
                    return {"estado_cadastral": 3, "id_cadastro": id_contrato}
                except Exception as err:
                    return err
            else:
                return 'É preciso conter o arquivo da imagem'
    else:
        return 'É nescessário inserir o id do contrato na url'


# Utilizado para pegar informação do contrato a partir do ID
@app.route('/info/<id_contrato>')
def info(id_contrato):
    if id_contrato:
        if mongo.db.contratos.find_one({"_id.id": ObjectId(id_contrato)}):
            contrato = mongo.db.contratos.find_one({"_id.id": ObjectId(id_contrato)})
            json_return = {'id': id_contrato,  
                            'nome': contrato['nome'], 
                            'email': contrato['email'], 
                            'valor_do_emprestimo': contrato['valor_do_emprestimo'], 
                            'dados_adicionais': {'renda': contrato['dados_adicionais']['renda'], 
                                                    'nascimento': contrato['dados_adicionais']['nascimento'], 
                                                    'estado_civil': contrato['dados_adicionais']['estado_civil'], 
                                                    'endereco': contrato['dados_adicionais']['endereco']}, 
                            'estado_cadastral': contrato['estado_cadastral'], 
                            'status': contrato['status'], 
                            'fotos': {'cpf': contrato['fotos']['cpf'], 
                                        'renda': contrato['fotos']['renda'], 
                                        'imovel': contrato['fotos']['imovel']}}
            return json_return
        else:
            return 'Não existe contrato nesse id'

    else:
        return 'É nescessário inserir o id do contrato na url'

# Esse endpoint serve apenas para visualizar a foto a partir do nome da foto
@app.route('/foto/<nome_da_foto>')
def foto(nome_da_foto):
    return mongo.send_file(nome_da_foto)
        

