import requests
from flask import Flask, render_template

app = Flask(__name__)

import datetime
import requests
from flask import Flask, jsonify, render_template
import sqlite3

# Criar conexão com o banco de dados
conn = sqlite3.connect('clientes.db')

# Criar tabela para os dados dos clientes
conn.execute('''CREATE TABLE IF NOT EXISTS clientes
                (id INTEGER PRIMARY KEY,
                nome TEXT NOT NULL,
                qtdMoeda INTEGER NOT NULL,
                flag INTEGER NOT NULL DEFAULT 0)''')

# Fechar a conexão com o banco de dados
conn.close()

def inserir_cliente(cliente):
    conn = sqlite3.connect('clientes.db')
    conn.execute('INSERT INTO clientes (id, nome, qtdMoeda, flag) VALUES (?, ?, ?, ?)', (cliente['id'], cliente['nome'], cliente['qtdMoeda'], cliente.get('flags', 0)))
    conn.commit()
    conn.close()


app = Flask(__name__)

def obter_ultima_transacao_id():
    url_transacoes = "http://127.0.0.1:5000/transacoes"
    response_transacoes = requests.get(url_transacoes)

    if response_transacoes.status_code == 200:
        transacoes_json = response_transacoes.json()
        ultimo_id = 0

        for transacao_id in transacoes_json:
            transacao_id_int = int(transacao_id)
            if transacao_id_int > ultimo_id:
                ultimo_id = transacao_id_int

        return ultimo_id

    return None
def obter_clientes():
    conn = sqlite3.connect('clientes.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clientes")
    rows = cursor.fetchall()
    clientes = []
    for row in rows:
        cliente = {
            'id': row[0],
            'nome': row[1],
            'qtdMoeda': row[2],
            'flags': row[3]
        }
        clientes.append(cliente)
    conn.close()
    return clientes

def verificar_flags(cliente_id):
    conn = sqlite3.connect('clientes.db')
    cursor = conn.cursor()
    cursor.execute("SELECT flag FROM clientes WHERE id = ?", (cliente_id,))
    row = cursor.fetchone()
    conn.close()
    if row is not None:
        return row[0]
    return 0

def validar_transacao(transacao):
    remetente_id = transacao['remetente']
    valor = transacao['valor']
    horario = transacao['horario']

    # Verificar saldo do remetente
    url_saldo_remetente = f"http://127.0.0.1:5000/cliente/{remetente_id}"
    response_saldo_remetente = requests.get(url_saldo_remetente)
    if response_saldo_remetente.status_code == 200:
        saldo_remetente = response_saldo_remetente.json()['qtdMoeda']
        if saldo_remetente < valor:
            # Atualizar a flag do cliente
            conn = sqlite3.connect('clientes.db')
            conn.execute('UPDATE clientes SET flag = flag + 1 WHERE id = ?', (remetente_id,))
            conn.commit()
            conn.close()
            return 0  # Saldo insuficiente

    # Verificar horário da transação
    horario_atual = datetime.datetime.now()
    if horario > horario_atual:
        # Atualizar a flag do cliente
        conn = sqlite3.connect('clientes.db')
        conn.execute('UPDATE clientes SET flag = flag + 1 WHERE id = ?', (remetente_id,))
        conn.commit()
        conn.close()
        return 0  # Horário inválido

    ultimo_transacao_id = obter_ultima_transacao_id()
    if ultimo_transacao_id is not None:
        if int(transacao['transacao_id']) <= ultimo_transacao_id:
            # Atualizar a flag do cliente
            conn = sqlite3.connect('clientes.db')
            conn.execute('UPDATE clientes SET flag = flag + 1 WHERE id = ?', (remetente_id,))
            conn.commit()
            conn.close()
            return 0  # Horário inválido

    # Verificar número de transações do remetente no último segundo
    url_num_transacoes = f"http://127.0.0.1:5000/transacoes/num/{remetente_id}"
    response_num_transacoes = requests.get(url_num_transacoes)
    if response_num_transacoes.status_code == 200:
        num_transacoes = response_num_transacoes.json()
        if num_transacoes >= 1000:
            # Atualizar a flag do cliente
            conn = sqlite3.connect('clientes.db')
            conn.execute('UPDATE clientes SET flag = flag + 1 WHERE id = ?', (remetente_id,))
            conn.commit()
            conn.close()
            return 0  # Limite de transações excedido

    return 1  # Transação válida


@app.route('/')
def index():
    # Obter a lista de clientes
    url_clientes = "http://127.0.0.1:5000/cliente"
    response_clientes = requests.get(url_clientes)
    clientes = obter_clientes()
    if not clientes:
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

                    # Inserir cliente no banco de dados
                    inserir_cliente(cliente)

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
    dados_clientes = []
    for cliente in clientes:
        dados_cliente = {
            "id": cliente['id'],
            "flags": cliente['flags'],
            "nome": cliente['nome'],
            "saldo": cliente['qtdMoeda']
        }
        dados_clientes.append(dados_cliente)

    return render_template('Validador.html', dados_clientes=dados_clientes)

if __name__ == '__main__':
    app.run(port=3600)
