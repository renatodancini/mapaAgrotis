from flask import Flask, request, render_template_string, send_file, redirect, url_for
import pandas as pd
import requests
import io
import os
import uuid
import sqlite3
from rapidfuzz import fuzz, process


app = Flask(__name__)

# HTML simples para upload/download
template = '''
<!doctype html>
<title>Atualizar Planilha</title>
<h2>Upload da Planilha (.xlsx)</h2>
<form method=post enctype=multipart/form-data>
  <input type=file name=file accept=".xlsx">
  <input type=submit value=Upload>
</form>
{% if download_url %}
  <h3>Download:</h3>
  <a href="{{ download_url }}">Baixar planilha atualizada</a>
{% endif %}
<br><br>
<a href="/produtos">Ver produtos cadastrados</a> |
<a href="/upload_planilha">Ver último upload da planilha</a> |
<a href="/comparativo">Comparativo de Produtos</a> |
<a href="/pesquisa_ia">Pesquisa IA</a>
'''

API_URL = "https://hom-receituariosipal.agrotis.io/int/fito/api/produtos"
API_TOKEN = "2795f2059403445e8808325d29336b4ac1770daeaa96c25879cb6d1d7d8582a82f65aeafb7d59366238b22be21ecece3d2093e3e98e1e5b4bd2c215d8a3ce95a"
TEMP_DIR = "temp_files"

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

DB_PATH = 'produtos.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS produtos (
        codMapaProduto TEXT PRIMARY KEY,
        nomeComum TEXT,
        principiosAtivos TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS Upload_planilha (
        Material TEXT,
        TextoBreveMaterial TEXT,
        Nivel2 TEXT,
        Mapa TEXT
    )''')
    conn.commit()
    conn.close()

def save_api_data_to_db(data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for item in data:
        cod = item.get('codMapaProduto')
        nome = item.get('nomeComum')
        principios = item.get('principiosAtivos')
        if cod:
            c.execute('''INSERT OR REPLACE INTO produtos (codMapaProduto, nomeComum, principiosAtivos) VALUES (?, ?, ?)''',
                      (cod, nome, principios))
    conn.commit()
    conn.close()

def save_planilha_to_db(df):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Limpa a tabela antes de inserir novos dados (opcional, remova se quiser manter histórico)
    c.execute('DELETE FROM Upload_planilha')
    for idx, row in df.iterrows():
        material = row[0]  # Coluna A
        texto_breve = row[1]  # Coluna B
        nivel2 = row[2] if len(row) > 2 else ''  # Coluna I (ajuste se necessário)
        mapa = row[3] if len(row) > 3 else ''  # Coluna S (ajuste se necessário)
        c.execute('''INSERT INTO Upload_planilha (Material, TextoBreveMaterial, Nivel2, Mapa) VALUES (?, ?, ?, ?)''',
                  (material, texto_breve, nivel2, mapa))
    conn.commit()
    conn.close()

def atualizar_mapa_upload_planilha():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Busca todos os produtos (nomeComum -> codMapaProduto)
    c.execute('SELECT nomeComum, codMapaProduto FROM produtos')
    produtos = {str(row[0]).strip(): row[1] for row in c.fetchall()}
    # Busca todos os uploads
    c.execute('SELECT rowid, TextoBreveMaterial FROM Upload_planilha')
    uploads = c.fetchall()
    for rowid, texto_breve in uploads:
        texto_breve = str(texto_breve).strip()
        cod_mapa = produtos.get(texto_breve, 'Não encontrado')
        c.execute('UPDATE Upload_planilha SET Mapa = ? WHERE rowid = ?', (cod_mapa, rowid))
    conn.commit()
    conn.close()

# Inicializa o banco ao iniciar o app
init_db()

# Adicione sua chave da Bing Web Search API aqui:
BING_API_KEY = 'SUA_CHAVE_AQUI'
BING_ENDPOINT = 'https://api.bing.microsoft.com/v7.0/search'

def buscar_na_web_bing(termo):
    headers = {"Ocp-Apim-Subscription-Key": BING_API_KEY}
    params = {"q": termo, "textDecorations": True, "textFormat": "HTML", "count": 5}
    response = requests.get(BING_ENDPOINT, headers=headers, params=params)
    results = []
    if response.status_code == 200:
        data = response.json()
        for item in data.get("webPages", {}).get("value", []):
            results.append({
                "title": item.get("name"),
                "url": item.get("url"),
                "snippet": item.get("snippet")
            })
    return results

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    download_url = None
    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.xlsx'):
            df = pd.read_excel(file)
            # Chama a API
            headers = {"x-auth-token": API_TOKEN}
            resp = requests.get(API_URL, headers=headers)
            data = resp.json()
            # Salva todos os dados da API no banco
            save_api_data_to_db(data)
            # Processa a planilha normalmente
            for idx, row in df.iterrows():
                texto_breve = str(row[1]).strip()  # Coluna B
                item = next((item for item in data if str(item.get('nomeComum', '')).strip() == texto_breve), None)
                cod_mapa = item.get('codMapaProduto') if item else ''
                df.iat[idx, 3] = cod_mapa  # Coluna S (índice 3)
            # Salva os dados da planilha no banco
            save_planilha_to_db(df)
            # Remover chamada automática após upload
            # atualizar_mapa_upload_planilha()
            # Salva em arquivo temporário
            file_id = str(uuid.uuid4())
            temp_path = os.path.join(TEMP_DIR, f"planilha_{file_id}.xlsx")
            df.to_excel(temp_path, index=False)
            download_url = url_for('download_file', filename=f"planilha_{file_id}.xlsx")
    return render_template_string(template, download_url=download_url)

@app.route('/produtos', methods=['GET', 'POST'])
def listar_produtos():
    termo = ''
    if request.method == 'POST':
        termo = request.form.get('termo', '').strip()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if termo:
        query = '''SELECT codMapaProduto, nomeComum, principiosAtivos FROM produtos
                   WHERE codMapaProduto LIKE ? OR nomeComum LIKE ? OR principiosAtivos LIKE ?'''
        like_termo = f"%{termo}%"
        c.execute(query, (like_termo, like_termo, like_termo))
    else:
        c.execute('SELECT codMapaProduto, nomeComum, principiosAtivos FROM produtos')
    produtos = c.fetchall()
    conn.close()
    # Renderiza a tabela HTML incluindo as colunas originais
    html = '''
    <!doctype html>
    <title>Lista de Produtos</title>
    <h2>Produtos cadastrados no banco</h2>
    <form method="post" action="/produtos" style="display:inline;">
        <input type="text" name="termo" placeholder="Pesquisar..." value="{{ termo }}">
        <button type="submit">Pesquisar</button>
    </form>
    <form method="post" action="/atualizar_produtos" style="display:inline; margin-left:10px;">
        <button type="submit">Atualizar produtos da API</button>
    </form>
    <form method="get" action="/exportar_produtos" style="display:inline; margin-left:10px;">
        <button type="submit">Exportar para XLSX</button>
    </form>
    <br><br>
    <table border="1" cellpadding="5" cellspacing="0">
      <tr>
        <th>codMapaProduto</th>
        <th>nomeComum</th>
        <th>principiosAtivos</th>
      </tr>
      {% for p in produtos %}
      <tr>
        <td>{{ p[0] }}</td>
        <td>{{ p[1] }}</td>
        <td>{{ p[2] }}</td>
      </tr>
      {% endfor %}
    </table>
    <br><a href="/">Voltar</a>
    '''
    from flask import render_template_string
    return render_template_string(html, produtos=produtos, termo=termo)

@app.route('/atualizar_produtos', methods=['POST'])
def atualizar_produtos():
    headers = {"x-auth-token": API_TOKEN}
    resp = requests.get(API_URL, headers=headers)
    data = resp.json()
    save_api_data_to_db(data)
    from flask import redirect, url_for
    return redirect(url_for('listar_produtos'))

@app.route('/exportar_produtos')
def exportar_produtos():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT codMapaProduto, nomeComum, principiosAtivos FROM produtos')
    produtos = c.fetchall()
    conn.close()
    import pandas as pd
    import io
    df = pd.DataFrame(produtos, columns=["codMapaProduto", "nomeComum", "principiosAtivos"])
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    from flask import send_file
    return send_file(output, as_attachment=True, download_name="produtos.xlsx")

@app.route('/upload_planilha')
def ver_upload_planilha():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT Material, TextoBreveMaterial, Nivel2, Mapa FROM Upload_planilha')
    dados = c.fetchall()
    conn.close()
    html = '''
    <!doctype html>
    <title>Dados do Último Upload da Planilha</title>
    <h2>Dados do Último Upload da Planilha</h2>
    <table border="1" cellpadding="5" cellspacing="0">
      <tr>
        <th>Material</th>
        <th>Texto Breve Material</th>
        <th>Nivel 2</th>
        <th>Mapa</th>
      </tr>
      {% for d in dados %}
      <tr>
        <td>{{ d[0] }}</td>
        <td>{{ d[1] }}</td>
        <td>{{ d[2] }}</td>
        <td>{{ d[3] }}</td>
      </tr>
      {% endfor %}
    </table>
    <br><a href="/">Voltar</a>
    '''
    from flask import render_template_string
    return render_template_string(html, dados=dados)

@app.route('/exportar_comparativo')
def exportar_comparativo():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Busca todos os dados do último upload
    c.execute('SELECT Material, TextoBreveMaterial, Nivel2 FROM Upload_planilha')
    planilha = c.fetchall()
    # Busca todos os produtos da API
    c.execute('SELECT codMapaProduto, nomeComum, principiosAtivos FROM produtos')
    produtos = c.fetchall()
    conn.close()
    produtos_dict = {}
    for p in produtos:
        nome = str(p[1]).strip().lower().split()[0] if p[1] else ''
        produtos_dict[nome] = p
    comparativo = []
    for linha in planilha:
        texto_breve = str(linha[1]).strip().lower().split()[0] if linha[1] else ''
        produto = produtos_dict.get(texto_breve)
        if produto:
            comparativo.append([linha[0], linha[1], linha[2], produto[0], produto[1], produto[2]])
        else:
            comparativo.append([linha[0], linha[1], linha[2], 'Não encontrado', 'Não encontrado', 'Não encontrado'])
    import pandas as pd
    import io
    df = pd.DataFrame(comparativo, columns=["Material", "Texto Breve Material", "Nivel 2", "codMapaProduto", "nomeComum", "principiosAtivos"])
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)
    from flask import send_file
    return send_file(output, as_attachment=True, download_name="comparativo_produtos.xlsx")

# Adicionar botão na página de comparativo
@app.route('/comparativo', methods=['GET', 'POST'])
def comparativo_produtos():
    if request.method == 'POST':
        atualizar_mapa_upload_planilha()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT Material, TextoBreveMaterial, Nivel2 FROM Upload_planilha')
    planilha = c.fetchall()
    c.execute('SELECT codMapaProduto, nomeComum, principiosAtivos FROM produtos')
    produtos = c.fetchall()
    conn.close()
    produtos_dict = {}
    for p in produtos:
        nome = str(p[1]).strip().lower().split()[0] if p[1] else ''
        produtos_dict[nome] = p
    comparativo = []
    for linha in planilha:
        texto_breve = str(linha[1]).strip().lower().split()[0] if linha[1] else ''
        produto = produtos_dict.get(texto_breve)
        if produto:
            comparativo.append((linha[0], linha[1], linha[2], produto[0], produto[1], produto[2]))
        else:
            comparativo.append((linha[0], linha[1], linha[2], 'Não encontrado', 'Não encontrado', 'Não encontrado'))
    html = '''
    <!doctype html>
    <title>Comparativo de Produtos</title>
    <h2>Comparativo de Produtos</h2>
    <form method="post" action="/comparativo" style="display:inline;">
        <button type="submit">Atualizar coluna MAPA do comparativo</button>
    </form>
    <form method="get" action="/exportar_comparativo" style="display:inline; margin-left:10px;">
        <button type="submit">Exportar para XLSX</button>
    </form>
    <br>
    <table border="1" cellpadding="5" cellspacing="0">
      <tr>
        <th colspan="3">Planilha</th>
        <th colspan="3">API</th>
      </tr>
      <tr>
        <th>Material</th>
        <th>Texto Breve Material</th>
        <th>Nivel 2</th>
        <th>codMapaProduto</th>
        <th>nomeComum</th>
        <th>principiosAtivos</th>
      </tr>
      {% for c in comparativo %}
      <tr>
        <td>{{ c[0] }}</td>
        <td>{{ c[1] }}</td>
        <td>{{ c[2] }}</td>
        <td>{{ c[3] }}</td>
        <td>{{ c[4] }}</td>
        <td>{{ c[5] }}</td>
      </tr>
      {% endfor %}
    </table>
    <br><a href="/">Voltar</a>
    '''
    from flask import render_template_string
    return render_template_string(html, comparativo=comparativo)

@app.route('/pesquisa_ia', methods=['GET', 'POST'])
def pesquisa_ia():
    resultados = []
    termo = ''
    web_results = []
    if request.method == 'POST':
        termo = request.form.get('termo', '').strip()
        if termo:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT codMapaProduto, nomeComum, principiosAtivos FROM produtos')
            produtos = c.fetchall()
            conn.close()
            # Busca fuzzy por nomeComum e principiosAtivos
            scored = []
            for p in produtos:
                score_nome = fuzz.token_set_ratio(termo.lower(), str(p[1]).lower())
                score_principio = fuzz.token_set_ratio(termo.lower(), str(p[2]).lower())
                score = max(score_nome, score_principio)
                if score > 50:
                    scored.append((score, p))
            scored.sort(reverse=True)
            resultados = [p for score, p in scored]
            # Se não houver resultados internos, busca na web
            if not resultados:
                web_results = buscar_na_web_bing(termo)
    html = '''
    <!doctype html>
    <title>Pesquisa IA</title>
    <h2>Pesquisa IA de Produtos</h2>
    <form method="post" action="/pesquisa_ia">
        <input type="text" name="termo" placeholder="Digite o termo ou pergunta..." value="{{ termo }}">
        <button type="submit">Pesquisar</button>
    </form>
    <br>
    {% if resultados %}
    <table border="1" cellpadding="5" cellspacing="0">
      <tr>
        <th>codMapaProduto</th>
        <th>nomeComum</th>
        <th>principiosAtivos</th>
      </tr>
      {% for r in resultados %}
      <tr>
        <td>{{ r[0] }}</td>
        <td>{{ r[1] }}</td>
        <td>{{ r[2] }}</td>
      </tr>
      {% endfor %}
    </table>
    {% elif termo and web_results %}
    <b>Nenhum resultado interno encontrado. Veja resultados da internet:</b><br><br>
    <ul>
      {% for w in web_results %}
      <li><a href="{{ w['url'] }}" target="_blank">{{ w['title'] }}</a><br>{{ w['snippet'] }}</li>
      {% endfor %}
    </ul>
    {% elif termo %}
    <b>Nenhum resultado encontrado.</b>
    {% endif %}
    <br><a href="/">Voltar</a>
    '''
    from flask import render_template_string
    return render_template_string(html, resultados=resultados, termo=termo, web_results=web_results)

@app.route('/download')
def download_file():
    filename = request.args.get('filename')
    if not filename:
        return "Nenhum arquivo processado.", 400
    temp_path = os.path.join(TEMP_DIR, filename)
    if not os.path.exists(temp_path):
        return "Arquivo não encontrado.", 404
    return send_file(temp_path, as_attachment=True, download_name="planilha_atualizada.xlsx")

if __name__ == '__main__':
    app.run(debug=True) 