import json
import requests
import random
import datetime
import ntplib
import hashlib
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

@app.route('/cliente/selecionar', methods=['GET'])
def selecionar_clientes():
    url_clientes = "http://127.0.0.1:5000/cliente"
    response_clientes = requests.get(url_clientes)

    if response_clientes.status_code == 200:
        clientes_json = response_clientes.json()
        clientes_ids = list(clientes_json.keys())

        # Selecionar três clientes aleatórios
        selecionados = random.sample(clientes_ids, 3)

        # Obter os detalhes dos clientes selecionados
        clientes_selecionados = []
        for cliente_id in selecionados:
            url_cliente = f"http://127.0.0.1:5000/cliente/{cliente_id}"
            response_cliente = requests.get(url_cliente)
            if response_cliente.status_code == 200:
                cliente_json = response_cliente.json()
                clientes_selecionados.append(cliente_json)

        # Obter as transações
        url_transacoes = "http://127.0.0.1:5000/transacoes"
        response_transacoes = requests.get(url_transacoes)

        if response_transacoes.status_code == 200:
            transacoes_json = response_transacoes.json()

            # Criar lista de transações no formato JSON
            transacoes_list = []
            processed_transactions = set()

            for cliente in clientes_selecionados:
                cliente_id = cliente['id']

                for transacao_id, transacao in transacoes_json.items():
                    # Skip if transaction ID has already been processed
                    if transacao_id in processed_transactions:
                        continue

                    if transacao['remetente'] == cliente_id or transacao['recebedor'] == cliente_id:
                        remetente_id = transacao['remetente']
                        recebedor_id = transacao['recebedor']
                        remetente_nome = clientes_json[str(remetente_id)]['nome']
                        recebedor_nome = clientes_json[str(recebedor_id)]['nome']

                        horario_transacao = pegar_horario()  # Gerar horário da transação
                        hash_transacao = gerar_hash(transacao_id, remetente_id, recebedor_id, transacao['valor'], horario_transacao)

                        transacao_data = {
                            "transacao_id": transacao_id,
                            "remetente": remetente_nome,
                            "id_remetente": remetente_id,
                            "recebedor": recebedor_nome,
                            "id_recebedor": recebedor_id,
                            "valor": transacao['valor'],
                            "horario": horario_transacao,
                            "flags": verificar_flags(remetente_id),
                            "hash": hash_transacao,
                        }

                        transacoes_list.append(transacao_data)

                        # Atualizar saldo do remetente
                        clientes_json[str(remetente_id)]['qtdMoeda'] -= transacao['valor']

                        # Atualizar saldo do recebedor
                        clientes_json[str(recebedor_id)]['qtdMoeda'] += transacao['valor']

                        # Add the processed transaction ID to the set
                        processed_transactions.add(transacao_id)


            return jsonify(transacoes_list)
        else:
            return jsonify({"error": f"Erro ao obter transações. Código de status: {response_transacoes.status_code}"})
    else:
        return jsonify({"error": f"Erro ao obter lista de clientes. Código de status: {response_clientes.status_code}"})

def pegar_horario():
    ntp_client = ntplib.NTPClient()
    response = ntp_client.request('pool.ntp.org')
    horario_transacao = datetime.datetime.fromtimestamp(response.tx_time)
    return horario_transacao.strftime("%Y-%m-%d %H:%M:%S")

def gerar_hash(transacao_id, remetente_id, recebedor_id, valor, horario_transacao):
    data = transacao_id + str(remetente_id) + str(recebedor_id) + str(valor) + horario_transacao
    hash_obj = hashlib.sha256(data.encode())
    return hash_obj.hexdigest()

def verificar_flags(remetente_id):
    # Lógica para verificar as flags do remetente
    # Substitua pelo código adequado
    return 0  # Exemplo de valor inteiro



@app.route('/')
def index():
    transacoes_json = selecionar_clientes()
    return render_template('index.html', transacoes_json=transacoes_json)

if __name__ == '__main__':
    app.run(port=3800)
