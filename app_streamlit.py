import streamlit as st
import pandas as pd
import sqlite3
from rapidfuzz import fuzz
import requests
import io
import os

# Configurações iniciais
BING_API_KEY = os.environ.get('BING_API_KEY', 'SUA_CHAVE_AQUI')  # Preferencialmente use variável de ambiente
BING_ENDPOINT = 'https://api.bing.microsoft.com/v7.0/search'
DB_PATH = 'produtos.db'
API_URL = "https://hom-receituariosipal.agrotis.io/int/fito/api/produtos"
API_TOKEN = "2795f2059403445e8808325d29336b4ac1770daeaa96c25879cb6d1d7d8582a82f65aeafb7d59366238b22be21ecece3d2093e3e98e1e5b4bd2c215d8a3ce95a"

# Funções auxiliares
def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
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

init_db()

def save_api_data_to_db(data):
    conn = get_conn()
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
    conn = get_conn()
    c = conn.cursor()
    c.execute('DELETE FROM Upload_planilha')
    for idx, row in df.iterrows():
        material = row[0]  # Coluna A
        texto_breve = row[1]  # Coluna B
        nivel2 = row[2] if len(row) > 2 else ''  # Coluna I
        mapa = row[3] if len(row) > 3 else ''  # Coluna S
        c.execute('''INSERT INTO Upload_planilha (Material, TextoBreveMaterial, Nivel2, Mapa) VALUES (?, ?, ?, ?)''',
                  (material, texto_breve, nivel2, mapa))
    conn.commit()
    conn.close()

def atualizar_mapa_upload_planilha():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT nomeComum, codMapaProduto FROM produtos')
    produtos = {str(row[0]).strip().lower().split()[0]: row[1] for row in c.fetchall()}
    c.execute('SELECT rowid, TextoBreveMaterial FROM Upload_planilha')
    uploads = c.fetchall()
    for rowid, texto_breve in uploads:
        chave = str(texto_breve).strip().lower().split()[0] if texto_breve else ''
        cod_mapa = produtos.get(chave, 'Não encontrado')
        c.execute('UPDATE Upload_planilha SET Mapa = ? WHERE rowid = ?', (cod_mapa, rowid))
    conn.commit()
    conn.close()

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

def atualizar_produtos_api():
    headers = {"x-auth-token": API_TOKEN}
    try:
        resp = requests.get(API_URL, headers=headers, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            save_api_data_to_db(data)
            return True
        else:
            st.error(f"Erro ao consultar a API! Status: {resp.status_code}")
            try:
                error_data = resp.json()
                st.error(f"Detalhes do erro: {error_data}")
            except:
                st.error(f"Resposta da API: {resp.text[:200]}...")
            return False
    except requests.exceptions.Timeout:
        st.error("Timeout ao consultar a API. O servidor demorou muito para responder.")
        return False
    except requests.exceptions.ConnectionError:
        st.error("Erro de conexão com a API. Verifique sua conexão com a internet.")
        return False
    except Exception as e:
        st.error(f"Erro inesperado ao consultar a API: {str(e)}")
        return False

# Lista de todas as abas possíveis
ALL_PAGES = [
    ("Home", "home"),
    ("Upload Planilha", "upload"),
    ("Produtos", "produtos"),
    ("Comparativo", "comparativo"),
    ("Pesquisa IA", "pesq_ia"),
]

# Adicionar tabela para controle de visibilidade do menu

def init_menu_links():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS menu_links (
        page_key TEXT PRIMARY KEY,
        visible INTEGER
    )''')
    # Inicializa com todas as páginas visíveis se a tabela estiver vazia
    c.execute('SELECT COUNT(*) FROM menu_links')
    if c.fetchone()[0] == 0:
        for _, key in ALL_PAGES:
            c.execute('INSERT INTO menu_links (page_key, visible) VALUES (?, ?)', (key, 1))
    conn.commit()
    conn.close()

init_menu_links()

def get_menu_visibility():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT page_key, visible FROM menu_links')
    result = {row[0]: bool(row[1]) for row in c.fetchall()}
    conn.close()
    return result

def set_menu_visibility(visibility_dict):
    conn = get_conn()
    c = conn.cursor()
    for key, visible in visibility_dict.items():
        c.execute('UPDATE menu_links SET visible = ? WHERE page_key = ?', (1 if visible else 0, key))
    conn.commit()
    conn.close()

# Interface Streamlit
st.set_page_config(page_title="Gestão de Produtos", layout="wide")
# st.title("Gestão de Produtos e Pesquisa IA")  # Removido o título principal

# Inicializa o estado das abas visíveis
if 'visible_pages' not in st.session_state:
    st.session_state['visible_pages'] = {k: True for _, k in ALL_PAGES}
if 'config_rerun' not in st.session_state:
    st.session_state['config_rerun'] = False

# Adiciona a aba de configuração
page_labels = [label for label, key in ALL_PAGES if st.session_state['visible_pages'][key] and key not in ['upload', 'produtos', 'comparativo']]
page_labels.append("Configuração")

# Menu lateral para navegação
menu_visibility = get_menu_visibility()
menu_labels = [label for label, key in ALL_PAGES if menu_visibility.get(key, True)] + ["Configuração"]
selected_page = st.sidebar.radio("Navegação", menu_labels, key="sidebar_menu")

# --- Página Home ---
if selected_page == "Home":
    # Card de status da API
    with st.container():
        st.markdown("""
            <div style='background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); padding: 10px 16px 10px 16px; margin-bottom: 18px;'>
        """, unsafe_allow_html=True)
        st.subheader("Status da API")
        if st.button("Verificar status da API", key="check_api_status"):
            try:
                headers = {"x-auth-token": API_TOKEN}
                resp = requests.get(API_URL, headers=headers, timeout=10)
                if resp.status_code == 200:
                    st.success("✅ API está funcionando normalmente!")
                else:
                    st.error(f"❌ API retornou erro {resp.status_code}")
                    try:
                        error_data = resp.json()
                        st.error(f"Detalhes: {error_data}")
                    except:
                        st.error(f"Resposta: {resp.text[:100]}...")
            except requests.exceptions.Timeout:
                st.error("⏰ Timeout - API demorou muito para responder")
            except requests.exceptions.ConnectionError:
                st.error("🌐 Erro de conexão - Verifique sua internet")
            except Exception as e:
                st.error(f"❌ Erro inesperado: {str(e)}")
        st.markdown("""</div>""", unsafe_allow_html=True)
    
    # Botão para download do template de carga
    with st.container():
        st.markdown("""
            <div style='background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); padding: 10px 16px 10px 16px; margin-bottom: 18px;'>
        """, unsafe_allow_html=True)
        import pandas as pd
        import io
        template_df = pd.DataFrame(columns=["Material", "TextoBreveMaterial", "Nivel2", "Mapa"])
        towrite_template = io.BytesIO()
        template_df.to_excel(towrite_template, index=False)
        st.download_button(
            label="Baixar template de carga (.xlsx)",
            data=towrite_template.getvalue(),
            file_name="template_upload.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_template_btn"
        )
        st.markdown("""</div>""", unsafe_allow_html=True)
    # Card de upload
    with st.container():
        st.markdown("""
            <div style='background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); padding: 16px 16px 8px 16px; margin-bottom: 18px;'>
        """, unsafe_allow_html=True)
        uploaded_file_home = st.file_uploader("Upload de planilha", type="xlsx", key="home_upload", label_visibility="collapsed")
        st.markdown("""</div>""", unsafe_allow_html=True)
        if uploaded_file_home:
            df_home = pd.read_excel(uploaded_file_home)
            st.write("Pré-visualização da planilha:", df_home.head())
            if st.button("Salvar no banco e atualizar produtos da API", key="home_btn_save"):
                save_planilha_to_db(df_home)
                # Barra de progresso para consulta e gravação da API
                progress = st.progress(0, text="Consultando API e atualizando banco de dados...")
                headers = {"x-auth-token": API_TOKEN}
                try:
                    resp = requests.get(API_URL, headers=headers, timeout=30)
                    if resp.status_code == 200:
                        data = resp.json()
                        total = len(data)
                        conn = get_conn()
                        c = conn.cursor()
                        for i, item in enumerate(data):
                            cod = item.get('codMapaProduto')
                            nome = item.get('nomeComum')
                            principios = item.get('principiosAtivos')
                            if cod:
                                c.execute('''INSERT OR REPLACE INTO produtos (codMapaProduto, nomeComum, principiosAtivos) VALUES (?, ?, ?)''',
                                          (cod, nome, principios))
                            if total > 0:
                                progress.progress(int((i+1)/total*100), text=f"Processando {i+1}/{total} produtos...")
                        conn.commit()
                        conn.close()
                        progress.progress(100, text="Finalizado!")
                    else:
                        st.error(f"Erro ao consultar a API! Status: {resp.status_code}")
                        try:
                            error_data = resp.json()
                            st.error(f"Detalhes do erro: {error_data}")
                        except:
                            st.error(f"Resposta da API: {resp.text[:200]}...")
                except requests.exceptions.Timeout:
                    st.error("Timeout ao consultar a API. O servidor demorou muito para responder.")
                except requests.exceptions.ConnectionError:
                    st.error("Erro de conexão com a API. Verifique sua conexão com a internet.")
                except Exception as e:
                    st.error(f"Erro inesperado ao consultar a API: {str(e)}")
                atualizar_mapa_upload_planilha()
                st.success("Planilha e produtos atualizados!")
    # Card de pesquisa IA
    with st.container():
        st.markdown("""
            <div style='background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); padding: 16px 16px 8px 16px; margin-bottom: 18px;'>
        """, unsafe_allow_html=True)
        termo_ia_home = st.text_input("Pesquisar produtos (IA)", key="pesq_ia_home")
        if termo_ia_home:
            conn = get_conn()
            produtos = pd.read_sql_query("SELECT codMapaProduto, nomeComum, principiosAtivos FROM produtos", conn)
            conn.close()
            scored = []
            for _, p in produtos.iterrows():
                score_nome = fuzz.token_set_ratio(termo_ia_home.lower(), str(p['nomeComum']).lower())
                score_principio = fuzz.token_set_ratio(termo_ia_home.lower(), str(p['principiosAtivos']).lower())
                score = max(score_nome, score_principio)
                if score > 50:
                    scored.append((score, p))
            scored.sort(key=lambda x: x[0], reverse=True)
            resultados = [p[1] for p in scored]
            if resultados:
                st.write("Resultados encontrados no banco:")
                st.dataframe(pd.DataFrame(resultados))
            else:
                st.write("Nenhum resultado interno encontrado. Veja resultados da internet:")
                web_results = buscar_na_web_bing(termo_ia_home)
                for w in web_results:
                    st.markdown(f"[{w['title']}]({w['url']})  \n{w['snippet']}")
        st.markdown("""</div>""", unsafe_allow_html=True)
    # Card do comparativo
    with st.container():
        st.markdown("""
            <div style='background: #fff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.07); padding: 16px 16px 8px 16px; margin-bottom: 18px;'>
        """, unsafe_allow_html=True)
        st.subheader("Comparativo de Produtos")
        conn = get_conn()
        planilha = pd.read_sql_query("SELECT Material, TextoBreveMaterial, Nivel2 FROM Upload_planilha", conn)
        produtos = pd.read_sql_query("SELECT codMapaProduto, nomeComum, principiosAtivos FROM produtos", conn)
        conn.close()
        produtos_dict = {str(p['nomeComum']).strip().lower().split()[0]: p for _, p in produtos.iterrows()}
        comparativo = []
        for _, linha in planilha.iterrows():
            chave = str(linha['TextoBreveMaterial']).strip().lower().split()[0] if linha['TextoBreveMaterial'] else ''
            produto = produtos_dict.get(chave)
            if produto is not None:
                comparativo.append([
                    linha['Material'], linha['TextoBreveMaterial'], linha['Nivel2'],
                    produto['codMapaProduto'], produto['nomeComum'], produto['principiosAtivos']
                ])
            else:
                comparativo.append([
                    linha['Material'], linha['TextoBreveMaterial'], linha['Nivel2'],
                    'Não encontrado', 'Não encontrado', 'Não encontrado'
                ])
        df_comp = pd.DataFrame(comparativo, columns=["Material", "Texto Breve Material", "Nivel 2", "codMapaProduto", "nomeComum", "principiosAtivos"])
        # Filtros
        st.subheader("Filtros do Comparativo")
        mostrar_nao_encontrados_home = st.checkbox("Exibir linhas 'Não encontrado' (Home)", value=True, key="home_filtro_nao_encontrado")
        if not mostrar_nao_encontrados_home:
            df_comp = df_comp[df_comp['codMapaProduto'] != 'Não encontrado']
        st.dataframe(df_comp)
        towrite = io.BytesIO()
        df_comp.to_excel(towrite, index=False)
        st.download_button("Exportar Comparativo para XLSX (Home)", towrite.getvalue(), "comparativo_produtos_home.xlsx", key="home_export_comp")
        st.markdown("""</div>""", unsafe_allow_html=True)

# --- Página Pesquisa IA ---
elif selected_page == "Pesquisa IA":
    st.header("Pesquisa IA de Produtos")
    termo_ia = st.text_input("Digite o termo ou pergunta para buscar produtos:", key="pesq_ia")
    if termo_ia:
        conn = get_conn()
        produtos = pd.read_sql_query("SELECT codMapaProduto, nomeComum, principiosAtivos FROM produtos", conn)
        conn.close()
        scored = []
        for _, p in produtos.iterrows():
            score_nome = fuzz.token_set_ratio(termo_ia.lower(), str(p['nomeComum']).lower())
            score_principio = fuzz.token_set_ratio(termo_ia.lower(), str(p['principiosAtivos']).lower())
            score = max(score_nome, score_principio)
            if score > 50:
                scored.append((score, p))
        scored.sort(key=lambda x: x[0], reverse=True)
        resultados = [p[1] for p in scored]
        if resultados:
            st.write("Resultados encontrados no banco:")
            st.dataframe(pd.DataFrame(resultados))
        else:
            st.write("Nenhum resultado interno encontrado. Veja resultados da internet:")
            web_results = buscar_na_web_bing(termo_ia)
            for w in web_results:
                st.markdown(f"[{w['title']}]({w['url']})  \n{w['snippet']}")

# --- Página Configuração ---
elif selected_page == "Configuração":
    # O login só é válido enquanto a aba de configuração está sendo executada
    if 'config_logged_in' not in st.session_state:
        st.session_state['config_logged_in'] = False
    if not st.session_state['config_logged_in']:
        st.header("Login necessário para acessar a Configuração")
        with st.form("config_login_form"):
            usuario = st.text_input("Usuário", key="login_user")
            senha = st.text_input("Senha", type="password", key="login_pass")
            submit = st.form_submit_button("Entrar")
        if submit:
            if usuario == "renato.dancini" and senha == "Sipal@501":
                st.session_state['config_logged_in'] = True
                st.success("Login realizado com sucesso!")
                st.rerun()
                st.stop()
            else:
                st.error("Usuário ou senha incorretos.")
        st.stop()
    # Conteúdo da aba de configuração (apenas se autenticado)
    st.header("Configuração de Páginas Visíveis no Menu")
    st.write("Selecione quais páginas devem ser exibidas no menu lateral e clique em 'Salvar alterações':")
    menu_visibility = get_menu_visibility()
    temp_visible = {}
    for label, key in ALL_PAGES:
        temp_visible[key] = st.checkbox(f"Exibir página: {label}", value=menu_visibility.get(key, True), key=f"config_{key}")
    if st.button("Salvar alterações", key="btn_salvar_config"):
        set_menu_visibility(temp_visible)
        st.rerun()
    st.info("As alterações só são aplicadas após clicar em 'Salvar alterações'.")

    # Exibir as abas ocultas como expanders dentro da configuração
    with st.expander("Upload Planilha"):
        st.header("Upload de Planilha .xlsx")
        uploaded_file = st.file_uploader("Escolha um arquivo .xlsx", type="xlsx", key="config_upload_upload")
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            st.write("Pré-visualização da planilha:", df.head())
            if st.button("Salvar no banco e atualizar produtos da API", key="config_btn_upload_upload"):
                save_planilha_to_db(df)
                atualizou = atualizar_produtos_api()
                atualizar_mapa_upload_planilha()
                st.success("Planilha e produtos atualizados!")
        st.subheader("Dados do último upload")
        conn = get_conn()
        planilha = pd.read_sql_query("SELECT * FROM Upload_planilha", conn)
        conn.close()
        st.dataframe(planilha)
        if not planilha.empty:
            towrite = io.BytesIO()
            planilha.to_excel(towrite, index=False)
            st.download_button("Exportar Upload para XLSX", towrite.getvalue(), "upload_planilha.xlsx", key="config_export_upload_upload")

    with st.expander("Produtos"):
        st.header("Produtos cadastrados no banco")
        if st.button("Atualizar produtos da API", key="config_btn_produtos_btn"):
            if atualizar_produtos_api():
                st.success("Produtos atualizados da API!")
            else:
                st.error("Erro ao atualizar produtos da API.")
        termo = st.text_input("Pesquisar produto (nome, código ou princípio ativo):", key="config_produtos_input")
        conn = get_conn()
        if termo:
            query = f"""
            SELECT codMapaProduto, nomeComum, principiosAtivos FROM produtos
            WHERE codMapaProduto LIKE ? OR nomeComum LIKE ? OR principiosAtivos LIKE ?
            """
            like_termo = f"%{termo}%"
            produtos = pd.read_sql_query(query, conn, params=(like_termo, like_termo, like_termo))
        else:
            produtos = pd.read_sql_query("SELECT codMapaProduto, nomeComum, principiosAtivos FROM produtos", conn)
        conn.close()
        st.dataframe(produtos)
        if not produtos.empty:
            towrite = io.BytesIO()
            produtos.to_excel(towrite, index=False)
            st.download_button("Exportar Produtos para XLSX", towrite.getvalue(), "produtos.xlsx", key="config_export_produtos_btn")

    with st.expander("Comparativo"):
        st.header("Comparativo de Produtos")
        conn = get_conn()
        planilha = pd.read_sql_query("SELECT Material, TextoBreveMaterial, Nivel2 FROM Upload_planilha", conn)
        produtos = pd.read_sql_query("SELECT codMapaProduto, nomeComum, principiosAtivos FROM produtos", conn)
        conn.close()
        produtos_dict = {str(p['nomeComum']).strip().lower().split()[0]: p for _, p in produtos.iterrows()}
        comparativo = []
        for _, linha in planilha.iterrows():
            chave = str(linha['TextoBreveMaterial']).strip().lower().split()[0] if linha['TextoBreveMaterial'] else ''
            produto = produtos_dict.get(chave)
            if produto is not None:
                comparativo.append([
                    linha['Material'], linha['TextoBreveMaterial'], linha['Nivel2'],
                    produto['codMapaProduto'], produto['nomeComum'], produto['principiosAtivos']
                ])
            else:
                comparativo.append([
                    linha['Material'], linha['TextoBreveMaterial'], linha['Nivel2'],
                    'Não encontrado', 'Não encontrado', 'Não encontrado'
                ])
        df_comp = pd.DataFrame(comparativo, columns=["Material", "Texto Breve Material", "Nivel 2", "codMapaProduto", "nomeComum", "principiosAtivos"])
        st.subheader("Filtros do Comparativo (Configuração)")
        mostrar_nao_encontrados = st.checkbox("Exibir linhas 'Não encontrado' (Configuração)", value=True, key="config_filtro_nao_encontrado_comp")
        if not mostrar_nao_encontrados:
            df_comp = df_comp[df_comp['codMapaProduto'] != 'Não encontrado']
        st.dataframe(df_comp)
        towrite = io.BytesIO()
        df_comp.to_excel(towrite, index=False)
        st.download_button("Exportar Comparativo para XLSX (Configuração)", towrite.getvalue(), "comparativo_produtos_config.xlsx", key="config_export_comp_comp")

# --- Outras páginas (Upload Planilha, Produtos, Comparativo) ---
# Se desejar, implemente as páginas específicas aqui, usando selected_page == "Upload Planilha", etc. 