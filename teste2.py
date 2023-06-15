# Atualizar os dados dos clientes no servidor
for cliente_id, cliente_data in clientes_json.items():
    url_atualizar_cliente = f"http://127.0.0.1:5000/cliente/{cliente_id}/{cliente_data['qtdMoeda']}"
    requests.post(url_atualizar_cliente)


import requests
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    # Obter a lista de clientes
    url_clientes = "http://127.0.0.1:5000/cliente"
    response_clientes = requests.get(url_clientes)

    if response_clientes.status_code == 200:
        clientes_json = response_clientes.json()

        # Atualizar o saldo de cada cliente com base nas transações
        for cliente_id, cliente in clientes_json.items():
            url_transacoes = f"http://127.0.0.1:5000/transacoes"
            response_transacoes = requests.get(url_transacoes)

            if response_transacoes.status_code == 200:
                transacoes_json = response_transacoes.json()
                saldo_atualizado = cliente['qtdMoeda']

                for transacao_id, transacao in transacoes_json.items():
                    if transacao['remetente'] == cliente_id:
                        saldo_atualizado -= transacao['valor']
                    if transacao['recebedor'] == cliente_id:
                        saldo_atualizado += transacao['valor']

                cliente['qtdMoeda'] = saldo_atualizado

                # Atualizar o saldo do cliente
                url_cliente = f"http://127.0.0.1:5000/cliente/{cliente_id}"
                response_atualizar = requests.post(url_cliente, json=cliente)

                if response_atualizar.status_code == 200:
                    print(f"Saldo atualizado para o cliente {cliente_id}")

        # Construir uma lista com os dados dos clientes
        dados_clientes = []
        for cliente_id, cliente in clientes_json.items():
            dados_cliente = {
                "id": cliente_id,
                "flags": verificar_flags(cliente_id),
                "nome": cliente['nome'],
                "saldo": cliente['qtdMoeda']
            }
            dados_clientes.append(dados_cliente)

        return render_template('Validador.html', dados_clientes=dados_clientes)
    else:
        return jsonify({"error": f"Erro ao obter lista de clientes. Código de status: {response_clientes.status_code}"})

def verificar_flags(cliente_id):
    # Lógica para verificar as flags do cliente
    # Substitua pelo código adequado
    return 0  # Exemplo de valor inteiro

if __name__ == '__main__':
    app.run(port=3600)
